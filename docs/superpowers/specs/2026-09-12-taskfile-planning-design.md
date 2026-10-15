# taskfile-planning — Design

**Date:** 2026-09-12
**Status:** Approved; ready for implementation planning.

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
| `WORKTREES <dir>` | GLOBAL | 0..1 | Directory for task worktrees, relative to the repo root. Default `.worktrees`. |
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
- **Parallel safety.** Each task runs in its own git worktree (section 4). Two tasks in the
  same wave must not have overlapping FILES, so their branches merge without conflicts.
- **Paths.** FILES and path globs are relative to the repository root. They mean the same
  thing in every worktree.

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

1. **Validate.** Run `ste_lint.py --json`. Refuse an invalid file. When `TASKLIST on`, mirror
   all tasks into the orchestrator's todo list.
2. **Prepare the workspace** (see "Worktree model" below). Require a clean working tree,
   apart from the Taskfile. Require the WORKTREES directory to be in `.gitignore`. Create
   or check out the integration branch.
3. **Reset interrupted tasks.** An `in_progress` task comes from an interrupted run. Rename
   its branch to `<branch>-attempt-<n>`, remove its worktree directory, and set it to
   `pending`. The old branch keeps its commits.
4. **For each wave, in order:**
   - Skip tasks at `completed_success`.
   - Mark a task whose dependency is `completed_failure` or `blocked` as
     `blocked BY <that dependency>`.
   - For each remaining task, create its worktree and branch from the current integration
     branch head. Set the task to `in_progress` and write the file.
   - Dispatch one subagent per task, never more than `AGENTS max` at once. Queue the rest
     and start one each time a slot frees.
   - Each subagent prompt contains: its worktree path; the GLOBAL block verbatim; its TASK
     block with `${}` values filled in from dependency OUTPUTs; and the FLOW contract.
   - For each report, run the checks in "Audit and merge" below. Write
     `completed_success`, or `completed_failure BECAUSE <reason>`.
   - Between waves, and whenever context usage passes the threshold, apply the COMPACT
     triggers. The Taskfile's STATUS lines are the source of truth. Re-read the file after
     compaction.
5. **Finish.** Print a table of each task's final STATUS, with BY chains, branch names, and
   the worktree path of each failed task. Stop. There are no automatic retries. A re-run
   skips completed tasks. The orchestrator never merges the integration branch into the
   user's branch. The user decides that.

### Worktree model

Every task runs in its own git worktree, so parallel tasks never share files. Git records
each task's work separately, and no work is lost.

| Item | Value |
|---|---|
| Base branch | The branch checked out when the run starts |
| Integration branch | `taskfile/<plan-name>/integration`, created from the base branch on the first run and reused on later runs |
| Integration worktree | `<WORKTREES>/<plan-name>/integration`. The orchestrator merges, verifies, and resets here. |
| Task branch | `taskfile/<plan-name>/tasks/<task-id>` |
| Task worktree | `<WORKTREES>/<plan-name>/tasks/<task-id>` |
| Taskfile | Stays in the main working tree. The orchestrator edits it there and does not commit STATUS changes. |

- The orchestrator creates worktrees with `git worktree add`. It does not use a harness
  isolation feature that picks its own paths or cleans up by itself, because the plan must
  control the names.
- A task branch starts from the integration branch after every earlier wave is merged. A
  task therefore sees the results of all its dependencies.
- The subagent works only in its worktree and commits there.

### Audit and merge

The orchestrator does these steps for each report, in the order that reports arrive. It
merges one task at a time.

1. **Save everything.** If the worktree has uncommitted changes, commit them as
   `<task-id>: uncommitted changes at report`.
2. **Attribute.** Compute `git diff --name-only <fork-point>..<task-branch>`. Every path must
   match the task's FILES. Otherwise the task fails
   `BECAUSE changed files outside FILES`.
3. **Verify in isolation.** Run each VERIFY command in the task worktree. Any non-zero exit
   fails the task. A report that claims success does not override this.
4. **Merge.** Merge the task branch into the integration branch with `--no-ff`. The commit
   message is `taskfile(<plan-name>): merge <task-id>`.
5. **Verify after the merge.** Run the task's VERIFY commands on the integration branch. If
   one fails, reset the integration branch to its commit before the merge. Fail the task
   `BECAUSE VERIFY failed after merge`. The task branch stays as it is.
6. **Clean up.** On success, remove the worktree directory and keep the branch. On failure,
   keep both the worktree and the branch so the user can inspect them.

The orchestrator owns the integration branch, so step 5 can reset it safely. It never resets
the base branch or a task branch.

**FLOW contract (sent to each subagent):**

- Work only in your worktree. Do not change the main working tree or another worktree.
- Commit your changes on your task branch before `report`. Do not merge, rebase, or push.
- Do the FLOW steps in order. Omit only the steps your SKIP lines name.
- Use only the TOOL named for each role.
- Stay inside PERMIT, DENY, and FILES.
- Do not start agents or subagents.
- Do not edit the Taskfile.
- Send a heartbeat after every n STEP lines when HEARTBEAT is set.
- End with `report`, including on failure.
- If your context runs out, report `completed_failure BECAUSE context limit`.

**Single writer.** Only the orchestrator edits the Taskfile and the integration branch, which
prevents races between parallel subagents. The orchestrator relays heartbeats to the user and never writes them to
the file.

## Error handling summary

| Situation | Behaviour |
|---|---|
| Invalid file | Mode 2 refuses to start and prints lint errors |
| Subagent failure | Task becomes `completed_failure`; dependents become `blocked BY` it; independent tasks continue |
| False success report | Orchestrator's VERIFY check fails the task |
| Subagent changes files outside FILES | The task-branch diff shows it; task becomes `completed_failure BECAUSE changed files outside FILES` |
| Subagent leaves uncommitted changes | Orchestrator commits them on the task branch, then audits |
| VERIFY passes in the worktree but fails after the merge | Integration branch resets to its pre-merge commit; task becomes `completed_failure BECAUSE VERIFY failed after merge` |
| Merge conflict | Should not occur, because FILES are disjoint within a wave. If it occurs, abort the merge and fail the task `BECAUSE merge conflict` |
| Dirty working tree or WORKTREES not ignored | Mode 2 refuses to start and names the problem |
| Interrupted run | The old task branch is renamed `-attempt-<n>`; the task resets to `pending` on the next run |
| Subagent context exhausted | `completed_failure BECAUSE context limit`; the user splits the task |

## Testing

- `tests/test_ste_lint.py`: fixtures per error code, golden waves, JSON shape.
- Skill behaviour: one scenario run per mode under `superpowers:writing-skills`, checking that
  Mode 1 stops at the run-now-or-later question, and that Mode 2 respects AGENTS max and writes
  `blocked BY`.
- Worktree model: a scenario run in a scratch repository with two parallel tasks and one
  dependent task. Check the branch names, one `--no-ff` merge per successful task, that a
  failed task keeps its worktree, and that a deliberate out-of-FILES edit fails the audit.

## Amendments (implementation plan, 2026-10-13)

- Git cannot hold `taskfile/<plan>` and `taskfile/<plan>/<id>` at once, so the branches are
  `taskfile/<plan>/integration` and `taskfile/<plan>/tasks/<id>`.
- Merges, post-merge VERIFY, and resets happen in an integration worktree. A reset in the
  main working tree would discard the Taskfile's uncommitted STATUS lines.
- The STE word checks skip UPPERCASE words, so `BECAUSE VERIFY failed after merge` is valid.
- `ste_lint.py --audit TASK_ID` reads changed paths on stdin and prints each path outside
  FILES. The attribution step uses it.
- An interrupted task's uncommitted changes are committed before its worktree is removed.
- A re-run skips `completed_failure` tasks as well as `completed_success` ones. SKILL.md
  gives the manual procedure to retry a failed task.
- The FLOW contract lets a subagent that cannot send messages during its run put its
  heartbeats in its report.
- A dependency is allowed when two tasks must change the same file.
- `--audit` exits 2 with errors on stderr for an invalid plan or an unknown task.
- `--audit` also reports paths under DENY write, GLOBAL or the task's own.
- Blocked tasks are never dispatched.
- WORKTREES is GLOBAL-only.
- COMPACT pct is 1..99.
- The attribution command is rename-safe:
  `git -c core.quotepath=off diff --no-renames --name-only <merge-base>..<branch>`.
- A `TOOL setup <command>` role, placed in FLOW before `verify`, prepares a fresh worktree.
  The orchestrator runs it before VERIFY in a task or integration worktree.
- On resume, the orchestrator aborts a merge in progress in the integration worktree. For
  an `in_progress` task whose merge commit (`taskfile(<plan>): merge <id>`) is on the
  integration branch, it runs VERIFY there instead of resetting the task. An ancestor
  check is not used, because a task branch with no commits is also an ancestor.
