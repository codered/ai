# NASA/DoD Deep Agent (LangChain) — Design Spec
**Date:** 2026-06-16
**Status:** Approved

---

## Overview

A standalone CLI tool built on **LangGraph** that performs iterative NASA/DOD-grade code review. Given a target directory, the agent:

1. Reviews all source code against NASA/DoD standards (using the existing `nasa-dod-code-review` skill bundled with this repo).
2. Scores the findings against a configurable rubric (P0–P3 severity thresholds).
3. If the rubric is not met, generates concrete code fixes via an LLM.
4. Applies the fixes, then re-reviews only the changed files.
5. Repeats until the rubric passes or a maximum iteration limit is reached.

The agent tracks its full state per-project in a `.nasa-dod-agent/` directory. If the process crashes or is interrupted, it resumes from its last checkpoint without re-reviewing files already processed.

- **Deployment:** Standalone Python CLI (not a pi plugin/skill).
- **LLM:** Any OpenAI-compatible API (base URL + model configurable).
- **Package manager:** `uv` (preferred user workflow is `uv run nasa-dod-agent review path/to/code`).

---

## Architecture

```
User CLI  ──►  LangGraph State Machine  ──►  LLM (+ file I/O)
             │                                   │
             │  ┌───────────────────────────┐   │
              │ review_code  │  evaluate_rubric  │ │
             │  │  generate_fixes    │                 │
             │  │  apply_fixes       │                 │
             │  │  re_review_changed │                 │
             └───────────────────────────┘   │
```

The agent is a **LangGraph `StateGraph`** with 5 nodes. Each node is a pure function that receives the current state, performs its work, and returns updates. The graph's edges define all routing — there is no LLM reasoning about "what to do next."

**State persistence (per-project):**

```
.nasa-dod-agent/
├── config.yaml          # user-defined rubric thresholds
├── state.json           # lightweight snapshot (findings summary, round #)
└── checkpoints/
    └── {thread_id}.sqlite  # full LangGraph checkpoint
```

The `state.json` is human-readable for quick resumption decisions; the SQLite checkpoint is fully delegated to LangGraph's serialization logic.

---

## Components & Graph Nodes

The graph state is a single `TypedDict` passed through every node.

### Node 1: `review_code`
Performs a NASA/DOD code review. Two modes:
- **Full scan** (first run, or `--full` flag) — reviews every file in the target directory.
- **Incremental scan** (subsequent loop iterations) — reviews only files listed in `state.last_modified_files`.

On a resume from checkpoint: if the last completed node was `review_code`, this node re-runs with its original parameters. If already past this node, it skips.

**State in:** `target_path`, `review_mode`  
**State out:** `findings: List[Finding]`, `files_reviewed: List[str]`

### Node 2: `evaluate_rubric`
Counts severity levels from findings. Compares against `config.yaml`:

```yaml
rubric:
  max_p0: 0
  max_p1: 2
  max_p2: 5
```

If all counts are ≤ thresholds, route to `END`. Otherwise, route to `generate_fixes`.

**State in:** `findings`, `config`  
**State out:** `rubric_passed: bool`, `p0_count`, `p1_count`, `p2_count`, `p3_count`

### Node 3: `generate_fixes`
For every finding with severity above the configured "fix threshold" (by default P0 + P1), prompts the LLM to produce a structured patch. Does **not** write to disk yet — just generates patches.

**State in:** `findings`, `rubric_passed`  
**State out:** `patches: List[Patch]`

### Node 4: `apply_fixes`
Applies `patches` to disk. Behavior per file:
1. Create `.bak` backup
2. Apply patch(es)
3. Record file as modified

**State in:** `patches`  
**State out:** `files_modified: List[str]`, `backup_paths: List[str]`

### Node 5: `re_review_changed`
Runs an incremental review of only `files_modified`. Produces new findings that replace the full findings list.

**State in:** `files_modified`  
**State out:** `findings: List[Finding]` (replacing the full list)

### Graph Routing

```
review_code ──► evaluate_rubric
                      │
              [pass?] ──► END
              [fail]  ──► generate_fixes ──► apply_fixes ──► re_review_changed
                                                   │
                                                   └── (loop back to evaluate_rubric)
```

All edges are deterministic — no LLM makes routing decisions.

### Additional Components

| Component | Role |
|-----------|------|
| **NASA/DoD Standards Loader** | Reads the skill's markdown files (`reviewer-prompt.md`, `severity-guide.md`, etc.) and formats them into the LLM system prompt for the review pass. Since this agent lives in the same repo as the skill, it references the canonical files from a bundled or relative path. |
| **LLM Client** | Thin wrapper around `langchain_openai.ChatOpenAI`. Base URL, API key, and model name are read from environment variables (`OPENAI_BASE_URL`, `OPENAI_API_KEY`) with a fallback in `config.yaml`. |
| **File System Saver** | A custom LangGraph `checkpointer` that writes SQLite checkpoints to `.nasa-dod-agent/checkpoints/{thread_id}.sqlite` after each node. On startup, checks for existing checkpoints and loads the latest if the user confirms. |
| **Fix Parser** | Ensures LLM-generated fixes are valid, parseable patches. If a patch is malformed, the node raises and the state remains clean (no disk changes applied). |

---

## Data Flow & Resume Logic

### Flow Model

```
INITIAL STATE (first run or fresh --reset):
  review_code (full) → evaluate → [pass END] → [fail] → generate → apply → re-review → evaluate → ...

RESUME STATE (after crash, user re-runs):
  Load checkpoint → restore state → determine next node → skip completed → proceed
```

There's no "resume from middle of a write" — `apply_fixes` is the only mutating node, and its behavior is atomic per file: backup → write → record. If it crashes mid-file, the next run detects the partial write and restores from `.bak` before resuming.

### State Schema (TypedDict)

```python
class GraphState(TypedDict):
    # Core workflow
    target_path: str
    review_mode: Literal["full", "incremental"]
    iteration: int              # 0-indexed, increments each loop
    max_iterations: int         # from config, default 10

    # Review findings
    findings: List[Finding]     # current set from latest review
    files_reviewed: List[str]   # all files seen so far
    last_modified_files: List[str]

    # Rubric
    config: RubricConfig        # loaded from config.yaml
    rubric_passed: bool

    # Fix artifacts
    patches: List[Patch]        # generated but not yet applied
    files_modified: List[str]   # files written to disk
    backup_paths: List[str]     # .bak files created
```

Everything in `GraphState` is JSON-serializable — this is the persistence contract.

### Resume Check on Startup

1. User runs: `uv run nasa-dod-agent review src/`
2. Check `.nasa-dod-agent/checkpoints/`
3. No checkpoint → default to fresh start
4. Checkpoint found:
   - Print: `"Found in-progress review for <target>."`
   - Show summary from `state.json`: iteration N, P0 count, P1 count, etc.
   - Ask: `"Resume from iteration N? (y/n)"`
   - `y` → load checkpoint, set LangGraph thread_id, proceed
   - `n` → fresh start (old checkpoint archived to `checkpoints/archive/`)

### Checkpoint File Lifecycle

| Event | Result |
|-------|--------|
| First run | `.nasa-dod-agent/checkpoints/review_{thread_id}.sqlite` created |
| During execution | file updated after every completed node |
| Success (END) | moved to `.nasa-dod-agent/checkpoints/archive/` |
| Failure / interrupt | stays in place for resume |
| User `--reset` | active checkpoints deleted; archives preserved |

---

## CLI Interface

```
Usage: nasa-dod-agent [OPTIONS] COMMAND [ARGS]...

Commands:
  review            Run the NASA/DOD review loop on a directory
  restore           Undo all agent changes (restore .bak files)
  status            Show current review state for target directory
  init-config       Generate a default config.yaml in .nasa-dod-agent/

Review options:
  PATH              Target directory to review
  --full            Force full scan (ignore any checkpoint state)
  --max-rounds N    Override config.yaml max_iterations
  --dry-run         Generate fixes but do not write to disk
  --reset           Delete active checkpoint, start fresh
  --no-interactive  Skip resume prompt; always start fresh if checkpoint exists
```

**Environment variables (required):**
- `OPENAI_API_KEY` — API key for the LLM
- `OPENAI_BASE_URL` — base URL for OpenAI-compatible endpoint (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` — model name (default: `gpt-4o`)

### Config File Format

`.nasa-dod-agent/config.yaml` (auto-generated if missing):

```yaml
rubric:
  max_p0: 0        # always zero for NASA/DOD
  max_p1: 2
  max_p2: 5
  max_p3: 999      # P3 never triggers a fix; informational only
  fix_threshold: 1   # 1 = fix P0+P1, 2 = fix P0+P1+P2, etc.

limits:
  max_iterations: 10

llm:
  temperature: 0.2  # deterministic for code generation
  max_tokens: 4096

exclude:
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/venv/**"
  - "**/__pycache__/**"
```

---

## Error Handling

### Review Node Failures
- **LLM API error** (rate limit, timeout) → pause graph, log error, save checkpoint. On resume, `review_code` retries with exponential backoff (already configured in `ChatOpenAI`).
- **Standards files missing** (bundled skill markdown not found) → hard fail on startup. This is a packaging bug, not runtime recoverable.

### Generate Fixes Node Failures
- **LLM produces malformed patches** (unparseable, wrong paths) → catch in `FixParser`, drop the bad patch, continue with the rest. Record failure as `PatchError` in state so the user sees it. Don't halt the whole review because one patch failed.
- **No patches generated but rubric failed** (all remaining findings are below fix_threshold but still above rubric limit) → route to termination with clear message: *"Rubric unmet but no fixable findings. Adjust fix_threshold or max_pX in config.yaml."*

### Apply Fixes Node Failures
- **Disk write error** (no permission, disk full) → raise, save checkpoint in pre-write state. User fixes disk issue, reruns.
- **File modified externally** (between generate and apply) → detect via timestamp/hash. Abort: *"File X was modified outside the agent. Resolve manually or use --reset."*

### Recovery Flags
```bash
uv run nasa-dod-agent review src/ --reset     # abandon current review, archive old checkpoint
uv run nasa-dod-agent restore                # undo all .bak restorations, clear backups
```

---

## Testing

| Test Category | What & How |
|---------------|-----------|
| **Unit — Graph Routing** | Feed constructed `GraphState` objects into `evaluate_rubric`. Assert correct branch. Mock LLM entirely. |
| **Unit — Fix Parser** | Feed malformed and well-formed LLM outputs. Assert valid parse, garbage filters. |
| **Unit — Checkpoint I/O** | Create temp directory, run nodes, verify SQLite files. Restart mid-flow, verify exact state restoration. |
| **Integration — Happy Path** | Point agent at known-bad sample project (deliberate NASA/DOD violations). Run until `END`. Assert final findings reduced. |
| **Integration — Resume** | SIGKILL after `apply_fixes`. Restart agent. Assert same final result as uninterrupted run. |
| **Integration — `restore`** | Let agent make changes, run `restore`. Assert `.bak` files restored. |

**Framework:** `pytest`.
**Unit tests:** mock `langchain` responses directly with `MagicMock`.
**Integration tests:** hit the real API using a tiny sample project to keep token costs down.

---

## Directory Structure

```
ai/
├── agents/
│   └── nasa-dod-agent/
│       ├── pyproject.toml           # uv project definition
│       ├── uv.lock                  # uv lockfile
│       ├── README.md                # usage guide
│       ├── src/
│       │   └── nasa_dod_agent/
│       │       ├── __init__.py
│       │       ├── cli.py             # Click (or typer) CLI entry point
│       │       ├── graph.py           # LangGraph state machine definition
│       │       ├── nodes/
│       │       │   ├── __init__.py
│       │       │   ├── review_code.py
│       │       │   ├── evaluate_rubric.py
│       │       │   ├── generate_fixes.py
│       │       │   ├── apply_fixes.py
│       │       │   └── re_review_changed.py
│       │       ├── models.py          # pydantic models: Finding, Patch, FindingPatch, etc.
│       │       ├── state.py           # GraphState TypedDict + StateUtils
│       │       ├── checkpointer.py    # FileSystemSaver: checkpoint to SQLite
│       │       ├── llm_client.py      # LangChain wrapper with retries + config
│       │       ├── standards_loader.py# Load bundled skill markdown into prompts
│       │       └── fix_parser.py      # Parse LLM output into apply-able patches
│       └── tests/
│           ├── __init__.py
│           ├── conftest.py
│           ├── test_graph_routing.py
│           ├── test_fix_parser.py
│           ├── test_checkpointer.py
│           ├── test_resume.py         # signall-based interrupt/resume test
│           └── fixtures/
│               └── bad_python_module/  # sample project with deliberate violations
└── docs/superpowers/specs/
    └── 2026-06-16-nasa-dod-agent-design.md  # this file
```

---

## Dependencies

```toml
[project]
name = "nasa-dod-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.0.50",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "pydantic>=2.0",
    "click>=8.0",          # CLI framework
    "pyyaml>=6.0",         # config.yaml parsing
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio",
    "ruff",               # lint/format
]
```

**Key dependency notes:**
- `langgraph` — the state machine framework. Pins to `>=0.0.50` for `checkpointer` support.
- `langchain-openai` — thin OpenAI-compatible wrapper. The user configures any `base_url` + `model`, so this works with local models, Azure, Together, etc.
- `click` — battle-tested CLI framework. Could swap for `typer` if team preference changes; no architectural difference.
- `pydantic` v2 for all data models (findings, patches, config, state).

---

## Key Design Decisions

1. **LangGraph over plain LangChain** — Checkpointing is first-class and idiomatic. Routing is explicit (type-safe graph edges) rather than an LLM deciding when to stop.
2. **Deterministic graph edges** — No LLM makes flow decisions. The only LLM calls are in `review_code`, `generate_fixes`, and `re_review_changed` — content nodes, not control nodes.
3. **Per-project `.nasa-dod-agent/` state** — Instance state for the project. Checkpoints are scoped to the project being reviewed, never global.
4. **Atomic file writes with `.bak`** — If `apply_fixes` crashes mid-file, the next run restores from `.bak` before overwriting. No partial file states leak across runs.
5. **OpenAI-compatible API** — Via `langchain-openai` + configurable `base_url`. Covers OpenAI, local LLMs (Ollama, vLLM), Azure, Together, etc. with one dependency.
6. **Bundled skill reference** — The agent reads the existing `nasa-dod-code-review` skill markdown files from a relative path. When the skill updates, the agent gets updated standards without code changes.
7. **Fix threshold independent of rubric threshold** — A user might accept up to 2 P1s (rubric), but still want the agent to *try* fixing all P1s. These are separate config values.
