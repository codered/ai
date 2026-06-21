# NASA/DoD Deep Agent

Iterative code review against NASA/DOD standards. Auto-fixes violations until a configurable rubric is met.

<p align="center">
  <img src="../../assets/demo/nasa-dod-agent/demo.gif" alt="The NASA/DoD Deep Agent reviewing a Go file with an unguarded divide-by-zero, generating a patch, applying it, and ending with a diff showing the zero-check it added" width="800">
  <br>
  <sub>A live run against a deliberately buggy file — review, patch, apply, then a diff of what changed. (<a href="../../assets/demo/nasa-dod-agent/demo.tape">regenerate with VHS</a>)</sub>
</p>

## Install

This project uses `uv` for dependency management. If you don't have `uv` installed:

```bash
curl -sSL https://astral.sh/uv/install.sh | sh
```

Then install the package in editable mode with dev dependencies:

```bash
cd agents/nasa-dod-agent
uv pip install -e ".[dev]"
```

## Quick Start

1. **Set your LLM credentials** (any OpenAI-compatible API):

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
export OPENAI_MODEL="gpt-4o"                        # optional, default: gpt-4o
```

2. **Target a codebase** and generate a config (optional but recommended):

```bash
nasa-dod-agent init-config path/to/code
```

3. **Start the review loop**:

```bash
nasa-dod-agent review path/to/code
```

After each completed review pass, a new `config.yaml` is generated:

```yaml
rubric:
  max_p0: 0
  max_p1: 2
  max_p2: 5
  max_p3: 999
  fix_threshold: 1

limits:
  max_iterations: 10

llm:
  temperature: 0.2
  max_tokens: 4096

exclude:
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/venv/**"
  - "**/__pycache__/**"
```

## Usage

```bash
# Review a directory (auto-generates .nasa-dod-agent/)
nasa-dod-agent review path/to/code

# Force a full scan from scratch, ignoring any existing checkpoints
nasa-dod-agent review path/to/code --full

# Only generate fixes; don't write to disk
nasa-dod-agent review path/to/code --dry-run

# Reset all checkpoints and start a fresh review
nasa-dod-agent review path/to/code --reset

# Skip the resume prompt (auto-resume if a checkpoint exists)
nasa-dod-agent review path/to/code --no-interactive

# Limit the number of review/fix loops
nasa-dod-agent review path/to/code --max-rounds 5

# Restore all files changed by the agent (from .bak backups)
nasa-dod-agent restore path/to/code

# Show current review progress for a directory
nasa-dod-agent status path/to/code

# Generate a default rubric config for a directory
nasa-dod-agent init-config path/to/code
```

## How It Works

The agent uses a **LangGraph** state machine with 5 nodes:

```
review_code  →  evaluate_rubric  → [FAIL] → generate_fixes  →  apply_fixes  →  re_review_changed
                      │                                              ↑
                      └── [PASS] → DONE ────────────────────────────┘
```

1. **review_code** — Scans all code files and calls the LLM to identify NASA/DOD violations.
2. **evaluate_rubric** — Counts findings by severity and checks if they're within your configured limits.
3. **generate_fixes** — For every P0/P1 finding, prompts the LLM to produce a concrete code patch.
4. **apply_fixes** — Applies patches atomically with a `.bak` backup in `.nasa-dod-agent/backups/`.
5. **re_review_changed** — Only re-reviews the files that were just modified, merging new findings with old ones.

The loop continues until the rubric passes, or until `max_iterations` is reached.

## Checkpointing & Resume

After each graph node, the agent's full state is saved as a JSON checkpoint in:

```
path/to/code/.nasa-dod-agent/
├── config.yaml         # your rubric thresholds
├── state.json          # human-readable progress summary
├── checkpoints/        # full LangGraph checkpoints
│   └── {thread_id}/
│       └── {checkpoint_id}.json
└── backups/            # .bak files for every file the agent modifies
```

If the process crashes or is interrupted, just re-run `nasa-dod-agent review path/to/code`. The agent detects the checkpoint and asks if you want to resume.

## Supported Languages

The file scanner looks for: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.c`, `.cpp`, `.h`, `.hpp`, `.go`, `.rs`, `.java`

Excluded by default: `node_modules`, `.git`, `venv`, `__pycache__`, `.nasa-dod-agent`

## Development

### Architecture

```
src/nasa_dod_agent/
├── __init__.py
├── cli.py                # Click CLI entry: review, restore, status
├── models.py             # pydantic v2 models: Finding, Patch, RubricConfig, etc.
├── config.py             # load/save .nasa-dod-agent/config.yaml
├── llm_client.py         # ChatOpenAI wrapper with env fallback
├── checkpointer.py       # FileSystemSaver: JSON checkpointing for LangGraph
├── fix_parser.py         # Parse markdown patches from LLM output; apply to disk
├── standards_loader.py  # Load bundled NASA/DOD skill markdown into prompts
├── state.py              # GraphState TypedDict
└── nodes/
    ├── review_code.py        # Node 1: full/incremental code review
    ├── evaluate_rubric.py   # Node 2: count severities, route pass/fail
    ├── generate_fixes.py    # Node 3: LLM patch generation
    ├── apply_fixes.py        # Node 4: atomic disk writes + .bak backups
    └── re_review_changed.py  # Node 5: incremental re-review of changed files
```

### Adding a New Node

1. Create `src/nasa_dod_agent/nodes/my_node.py`.
2. Define a function `my_node(state: GraphState) -> dict` that returns the keys you want to update in state.
3. Import it in `graph.py`, add it via `workflow.add_node("my_node", my_node)`, and wire up the edges.

### Running Tests

```bash
cd agents/nasa-dod-agent
.venv/bin/python -m pytest tests/ -v
```

To run tests for a single file:
```bash
.venv/bin/python -m pytest tests/test_fix_parser.py -v
```

### Adding Tests

Every new feature needs a failing test first. Tests live in `tests/` and use `pytest`. The `temp_project` fixture (from `conftest.py`) gives you a clean temp directory for disk operations.

### Vendored Standards

The agent bundles the NASA/DOD skill markdown from this repo's `pi-skills`:

```
standards/
├── reviewer-prompt.md    # Analysis instructions for the code review pass
└── severity-guide.md     # P0–P3 definitions with concrete examples
```

If you want to update the review logic, edit these markdown files — the agent reads them at runtime and injects them into the LLM system prompt.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | API key for the LLM |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | No | `gpt-4o` | Model name |

## Troubleshooting

**File not found: `nasa-dod-agent`**
→ Make sure you installed in editable mode: `uv pip install -e ".[dev]"`

**No backups found when restoring**
→ The agent only creates backups when it applies patches. Run a review first.

**Resume prompt keeps showing**
→ Use `--no-interactive` to skip the prompt. Use `--reset` to discard the checkpoint.
