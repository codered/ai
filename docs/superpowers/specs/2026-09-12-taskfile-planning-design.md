# taskfile-planning — Design

**Date:** 2026-09-12
**Status:** Approved in brainstorming; awaiting spec review.

## Purpose

`taskfile-planning` is a skill that writes and runs a `Taskfile.ste`: a line-oriented,
Dockerfile-style plan for LLM work. One GLOBAL block fixes environment, stack, permissions,
tools, and the working method (FLOW). One or more TASK blocks describe units of work. Tasks
declare Terraform-style dependencies, so independent tasks run in parallel waves.

Every prose line is written in ASD-STE100 Simplified Technical English, so a subagent reads
exactly one meaning.

Agents consume the file as instructions. There is no separate runtime. A stdlib Python
validator makes the format strict, and the skill's run mode defines how an orchestrator
executes it.

## Non-goals

- A standalone CLI executor or daemon.
- Automatic retries of failed tasks.
- Nested orchestration: subagents never start agents.
- Semantic STE checks a program cannot count (for example, active voice). The model applies
  those while authoring.

## Skill layout

    skills/taskfile-planning/
      SKILL.md                  both modes, trigger phrases, the FLOW contract
      references/
        format.md               full grammar, directive table, semantics, examples
        ste_lint.py             validator (stdlib only, single file)
        example.ste             valid golden example
      tests/
        test_ste_lint.py
        fixtures/*.ste          one fixture per error code, plus valid files

STE rules come from `skills/nfc/references/style-rules.md`. `ste_lint.py` embeds only the
countable subset as a table at the top of the script.

## 1. File format

### Lexical rules

- Line-oriented. One directive per line: an UPPERCASE keyword, then arguments.
- `#` starts a comment, either on a line of its own or after whitespace.
- Blank lines are ignored. Indentation is cosmetic.
- There is no line continuation. Long prose becomes more STEP lines.
- Blocks: `GLOBAL` … `END`, and `TASK <id>` … `END`. Blocks do not nest.
- Task ids match `[a-z][a-z0-9-]*` and are unique.

### Directives

| Directive | Scope | Count | Meaning |
|---|---|---|---|
| `PLAN <name> <version>` | file top | 1, first line | Plan identity |
| `ENV <k>=<v> …` | GLOBAL | 0..n | Environment facts |
| `STACK <item> …` | GLOBAL | 0..n | Tech stack |
| `TOOL <role> <command…>` | GLOBAL | 1..n | The one tool for a role (edit, fmt, build…). Roles are unique. |
| `FLOW <step> -> <step> …` | GLOBAL | 1 | Ordered steps every task runs |
| `RULE <sentence>` | GLOBAL | 0..n | Methodology rule, in STE |
| `AGENTS max <n>` | GLOBAL | 1 | Maximum concurrent subagents, n ≥ 1 |
| `HEARTBEAT every <n> steps` | GLOBAL | 0..1 | Subagent sends a heartbeat after every n STEP lines |
| `COMPACT when context > <pct>%` | GLOBAL | 0..1 | Orchestrator compacts at this context usage |
| `COMPACT after wave` | GLOBAL | 0..1 | Orchestrator compacts between waves |
| `TASKLIST on\|off` | GLOBAL | 0..1 | Orchestrator mirrors tasks into its todo list. Default off. |
| `PERMIT <action> <glob…>` | GLOBAL, TASK | 0..n | Allow an action. In a TASK, narrowing only. |
| `DENY <action> <glob…>` | GLOBAL, TASK | 0..n | Forbid an action. A TASK may only add restrictions. |
| `DEPENDS <id> …` | TASK | 0..n | Explicit dependency |
| `GOAL <sentence>` | TASK | 1 | Result of the task, in STE |
| `STEP <sentence>` | TASK | 0..n | Ordered instruction, in STE |
| `FILES <glob…>` | TASK | 1..n | Files the task may change |
| `OUTPUT <key> = <value>` | TASK | 0..n | Value other tasks read as `${id.key}` |
| `SKIP <flow-step> BECAUSE <sentence>` | TASK | 0..n | Omit one FLOW step, with a reason |
| `VERIFY <command…>` | TASK | 1..n | Command that must exit 0 |
| `STATUS <state> [BECAUSE <sentence>] [BY <id>]` | TASK | 0..1 | Execution state. Only the orchestrator writes it. |

Permission actions: `read`, `write`, `run`, `network`. `network` takes no glob, or host
globs. `spawn` is reserved: every task has an implicit `DENY spawn`, and any `PERMIT spawn`
is an error.

### FLOW steps

A FLOW step is a TOOL role declared in GLOBAL or one of these built-ins:

| Built-in | The subagent does this |
|---|---|
| `read` | Reads its FILES and the targets its dependencies' OUTPUT values name |
| `tasklist` | Loads its STEP lines into its todo list and marks each done |
| `heartbeat` | Sends the orchestrator one line: task id, current step, `in_progress` |
| `verify` | Runs every VERIFY command; all must exit 0 |
| `report` | Sends the final state, VERIFY output, and changed files to the orchestrator |

`report` always runs last, whether or not FLOW lists it. `verify` and `report` cannot be
skipped. Compaction is not a FLOW step. It belongs to the orchestrator only (see section 4).

### States

`pending` (the default when STATUS is absent), `in_progress`, `completed_success`,
`completed_failure` (requires BECAUSE), `blocked` (requires BY <id>).

`BY` names the direct dependency that failed or is blocked. Following BY links reaches the
root failure.

### Semantics

- **Inheritance.** A task inherits all of GLOBAL. A task cannot contain ENV, STACK, TOOL,
  FLOW, RULE, AGENTS, HEARTBEAT, COMPACT, or TASKLIST.
- **Narrow-only permissions.** Every task PERMIT must be a subset of a global PERMIT for the
  same action. Every task FILES glob must be a subset of the effective write PERMIT.
- **Dependency graph.** Edges come from DEPENDS and from every `${id.key}` in the task's
  text. Waves are the topological levels of the graph.
- **Parallel safety.** Two tasks in the same wave must not have overlapping FILES.

### Example

    PLAN health-check 1

    GLOBAL
      ENV        os=linux python=3.12
      STACK      fastapi postgres
      AGENTS     max 3
      PERMIT     read **
      PERMIT     write src/** tests/** migrations/**
      PERMIT     run uv pytest ruff
      DENY       network
      TOOL edit  hashline
      TOOL fmt   ruff format
      TOOL build uv build
      FLOW       read -> tasklist -> edit -> fmt -> build -> verify -> report
      RULE       Do not change files outside FILES.
      HEARTBEAT  every 2 steps
      COMPACT    after wave
      TASKLIST   on
    END

    TASK schema
      GOAL      Add the table "health_log".
      FILES     migrations/004_health.sql
      OUTPUT    table = health_log
      VERIFY    pytest tests/test_migrations.py
      STATUS    completed_success
    END

    TASK endpoint
      DEPENDS   schema
      GOAL      Add the GET /health endpoint.
      STEP      Write one row to ${schema.table} for each request.
      FILES     src/api.py tests/test_health.py
      SKIP      build BECAUSE This task does not change the package.
      VERIFY    pytest tests/test_health.py
    END

## 2. Validator: `ste_lint.py`

**Interface:** `python3 ste_lint.py <file> [--waves] [--json]`

- Exit 0: valid. Exit 1: errors, one per line as `file:line: CODE message`. Exit 2: usage or
  IO error.
- `--waves` prints `wave N: id id …`, one line per wave.
- `--json` prints `{plan, global, tasks, waves}` for the orchestrator. The orchestrator
  never parses the file itself.

**Checks:**

| Prefix | Class | Checks |
|---|---|---|
| S | Structure | PLAN first; exactly one GLOBAL; blocks closed; known keywords; directive in an allowed scope; count limits; id format and uniqueness; required directives present (AGENTS, FLOW, GOAL, FILES, VERIFY) |
| G | Graph | DEPENDS and `${}` targets exist; `${id.key}` names a declared OUTPUT; no cycles; no FILES overlap within a wave |
| P | Permissions | Task PERMIT ⊆ global PERMIT; FILES ⊆ write PERMIT; no PERMIT that a DENY forbids; no `PERMIT spawn`; the first word of each VERIFY command matches a `PERMIT run` glob |
| F | Flow | FLOW steps are declared roles or built-ins; SKIP names a FLOW step; no SKIP of verify or report; TOOL roles unique |
| T | STE | On GOAL, STEP, RULE, and BECAUSE text: ≤ 20 words per sentence; no banned or vague words; no leading gerund |
| X | Status | Valid state; BECAUSE with completed_failure; BY with blocked; BY target is a dependency in state completed_failure or blocked; no in_progress or completed_* task with a dependency that is not completed_success |

**Glob subset rule (conservative):** a task glob is inside a global glob only when the global
glob's literal prefix contains it and the global glob's wildcard part matches everything
under that prefix (`src/**` contains `src/api.py` and `src/*.py`). If the validator cannot
decide, it reports an error saying so. It never guesses in favour of the task.

**Tests:** one fixture per error code, each asserting its exact error line. The golden
`example.ste` asserts exit 0 and exact `--waves` output. A valid file with a 3-wave graph
checks the wave computation.

## 3. Mode 1: Author

**Triggers:** "write a taskfile", "plan this as a Taskfile.ste", "taskfile-planning".

1. **Globals.** Read the repo (lockfiles, CI config, formatter config) and propose ENV, STACK,
   TOOL, and FLOW. Confirm them in one message. Ask directly for what the repo does not
   show: permissions (especially `network` and paths outside the repo), AGENTS max, and FLOW
   order.
2. **Tasks.** Each task is one unit that one subagent can finish and verify within its own
   context. Add a dependency only when a task consumes another's result. Give each task the
   narrowest FILES.
3. **STE.** Write GOAL, STEP, RULE, and BECAUSE text under the `nfc` strict rules.
4. **Lint loop.** Run `ste_lint.py` until it exits 0. Never widen a global permission to
   pass a check without asking the user.
5. **Present and stop.** Show the path, the `--waves` output, and one line per task. Ask:
   "Run this plan now, or later?" On "later", stop and give the command to run it
   ("run Taskfile.ste"). Mode 2 never starts without an explicit yes.

**Location:** `Taskfile.ste` at the repo root. Use `plans/<name>.ste` when a Taskfile exists or
the user wants several plans. Never overwrite an existing file without asking.

## 4. Mode 2: Run (orchestrator)

**Start:** only on an explicit request, from the author prompt or a later "run <file>".

1. **Validate.** Run `ste_lint.py --json`. Refuse an invalid file. Reset `in_progress` tasks
   to `pending` (they come from an interrupted run). When `TASKLIST on`, mirror all tasks
   into the orchestrator's todo list.
2. **For each wave, in order:**
   - Skip tasks at `completed_success`.
   - Mark a task whose dependency is `completed_failure` or `blocked` as
     `blocked BY <that dependency>`.
   - Set the other tasks to `in_progress` and write the file.
   - Dispatch one subagent per task, never more than `AGENTS max` at once. Queue the rest
     and start one each time a slot frees.
   - Each subagent prompt contains: the GLOBAL block verbatim; its TASK block with `${}`
     values filled in from dependency OUTPUTs; and the FLOW contract.
   - For each report: confirm the VERIFY evidence and that changed files ⊆ FILES. Re-run
     VERIFY when the evidence is missing. Write `completed_success`, or
     `completed_failure BECAUSE <reason>`. A report that claims success but fails VERIFY is a
     failure.
   - Between waves, and whenever context usage passes the threshold, apply the COMPACT
     triggers. The Taskfile's STATUS lines are the source of truth. Re-read the file after
     compaction.
3. **Finish.** Print a table of each task's final STATUS, with BY chains, and stop. There
   are no automatic retries. A re-run skips completed tasks.

**FLOW contract (sent to each subagent):**

- Do the FLOW steps in order. Omit only the steps your SKIP lines name.
- Use only the TOOL named for each role.
- Stay inside PERMIT, DENY, and FILES.
- Do not start agents or subagents.
- Do not edit the Taskfile.
- Send a heartbeat after every n STEP lines when HEARTBEAT is set.
- End with `report`, including on failure.
- If your context runs out, report `completed_failure BECAUSE context limit`.

**Single writer.** Only the orchestrator edits the Taskfile, which prevents races between
parallel subagents. The orchestrator relays heartbeats to the user and never writes them to
the file.

## Error handling summary

| Situation | Behaviour |
|---|---|
| Invalid file | Mode 2 refuses to start and prints lint errors |
| Subagent failure | Task becomes `completed_failure`; dependents become `blocked BY` it; independent tasks continue |
| False success report | Orchestrator's VERIFY check fails the task |
| Subagent changes files outside FILES | Task becomes `completed_failure BECAUSE changed files outside FILES` |
| Interrupted run | `in_progress` resets to `pending` on the next run |
| Subagent context exhausted | `completed_failure BECAUSE context limit`; the user splits the task |

## Testing

- `tests/test_ste_lint.py`: fixtures per error code, golden waves, JSON shape.
- Skill behaviour: one scenario run per mode under `superpowers:writing-skills`, checking that
  Mode 1 stops at the run-now-or-later question, and that Mode 2 respects AGENTS max and writes
  `blocked BY`.
