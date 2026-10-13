# Taskfile.ste format

Reference for `skills/taskfile-planning/SKILL.md`. Load this file when you write a
Taskfile, fix a lint error, or need the exact meaning of a directive.

## Lexical rules

- The file is line-oriented. Each line holds one directive: an UPPERCASE keyword, then
  its arguments.
- `#` starts a comment when it is the first character of a line or follows whitespace.
  `src/a#b.py` contains no comment.
- Blank lines are ignored. Indentation is cosmetic.
- There is no line continuation. Write long prose as more STEP lines.
- Blocks are `GLOBAL` … `END` and `TASK <id>` … `END`. Blocks do not nest.
- Task ids and the plan name match `[a-z][a-z0-9-]*`. Task ids are unique.

## Directives

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
| `COMPACT when context > <pct>%` | GLOBAL | 0..1 | Orchestrator compacts at this context usage, 1 ≤ pct ≤ 99 |
| `COMPACT after wave` | GLOBAL | 0..1 | Orchestrator compacts between waves |
| `TASKLIST on\|off` | GLOBAL | 0..1 | Orchestrator mirrors tasks into its todo list. Default off. |
| `WORKTREES <dir>` | GLOBAL | 0..1 | Directory for worktrees, relative to the repo root. Default `.worktrees`. |
| `PERMIT <action> <glob…>` | GLOBAL, TASK | 0..n | Allow an action. In a TASK, narrowing only. |
| `DENY <action> <glob…>` | GLOBAL, TASK | 0..n | Forbid an action. A TASK may only add restrictions. |
| `DEPENDS <id> …` | TASK | 0..n | Explicit dependency |
| `GOAL <sentence>` | TASK | 1 | Result of the task, in STE |
| `STEP <sentence>` | TASK | 0..n | Ordered instruction, in STE |
| `FILES <glob…>` | TASK | 1..n | Files the task may change |
| `OUTPUT <key> = <value>` | TASK | 0..n | Value other tasks read as `${id.key}`. Keys are unique per task. |
| `SKIP <flow-step> BECAUSE <sentence>` | TASK | 0..n | Omit one FLOW step, with a reason |
| `VERIFY <command…>` | TASK | 1..n | Command that must exit 0 |
| `STATUS <state> [BECAUSE <sentence>] [BY <id>]` | TASK | 0..1 | Execution state. Only the orchestrator writes it. |

## Permissions

Actions: `read`, `write`, `run`, `network`, `spawn`.

- `read`, `write`, and `run` need at least one glob. A `run` glob matches a program name,
  for example `pytest` or `py*`.
- `network` takes no glob, which means every host, or host globs.
- `spawn` is reserved. Every task has an implicit `DENY spawn`. `PERMIT spawn` is an error.
- A task with no PERMIT for an action uses the GLOBAL PERMIT globs for that action. A task
  with a PERMIT for an action uses only its own globs, and each one must be inside a
  GLOBAL PERMIT for the same action.
- GLOBAL DENY lines apply to every task.

## Globs

- `**` matches across directories. `*` and `?` match inside one directory.
- Paths are relative to the repository root. They mean the same thing in every worktree.
- **Subset rule.** Glob A is inside glob B when B's literal prefix contains A, and B's
  wildcard part is exactly `**`. `src/**` contains `src/api.py` and `src/*.py`. A literal
  path is inside B when B matches it. If the linter cannot decide, it reports an error.
  It never decides in favour of the task.
- **DENY rule.** A PERMIT or FILES glob fails only when a DENY glob contains it fully.
  `PERMIT write src/**` with `DENY write src/secrets/**` is valid.
- **Overlap rule.** Two FILES globs overlap when one literal prefix starts the other.
  The rule is conservative: `src/*.py` and `src/*.md` overlap.

## FLOW steps

A FLOW step is a TOOL role declared in GLOBAL or one of these built-ins:

| Built-in | The subagent does this |
|---|---|
| `read` | Reads its FILES and the targets its dependencies' OUTPUT values name |
| `tasklist` | Loads its STEP lines into its todo list and marks each done |
| `heartbeat` | Sends the orchestrator one line: task id, current step, `in_progress` |
| `verify` | Runs every VERIFY command; all must exit 0 |
| `report` | Sends the final state, VERIFY output, and changed files to the orchestrator |

`report` always runs last, whether or not FLOW lists it. `verify` and `report` cannot be
skipped. Compaction is not a FLOW step. Only the orchestrator compacts.

## States

| State | Meaning | Needs |
|---|---|---|
| `pending` | Not started. The default when STATUS is absent. | — |
| `in_progress` | Dispatched. On a new run, this means the last run stopped. | — |
| `completed_success` | Audited, verified, and merged | — |
| `completed_failure` | Failed | `BECAUSE <sentence>` |
| `blocked` | A dependency failed or is blocked | `BY <id>` |

`BY` names the direct dependency that failed or is blocked. Follow the BY links to find
the root failure.

## Semantics

- **Inheritance.** A task inherits all of GLOBAL. A task cannot contain ENV, STACK, TOOL,
  FLOW, RULE, AGENTS, HEARTBEAT, COMPACT, TASKLIST, or WORKTREES.
- **Dependency graph.** Edges come from DEPENDS and from every `${id.key}` in the task's
  text. Waves are the topological levels of the graph: a task with no dependencies is in
  wave 1, and every other task is one wave after its latest dependency.
- **Parallel safety.** Each task runs in its own git worktree. Two tasks in the same wave
  must not have overlapping FILES, so their branches merge without conflicts.

## STE checks

The linter checks GOAL, STEP, RULE, and BECAUSE text. It counts only the mechanical rules
from `skills/nfc/references/style-rules.md`:

- A sentence has 20 words or fewer. Quoted text, backticked text, and `${id.key}` each
  count as one word.
- No rejected word from the substitution table, such as "ensure" or "prior to". The error
  names the approved word.
- No word that adds no meaning, such as "just" or "basically".
- No sentence starts with an `-ing` word.

Quoted text, backticked text, `${id.key}`, and UPPERCASE words are not checked for
rejected words. `VERIFY failed after merge` is valid. Apply the other STE rules, such as
the active voice, yourself.

## Error codes

Each error prints as `FILE:LINE: CODE message`.

| Code | Meaning |
|---|---|
| S001 | PLAN must be the first directive and appear once |
| S002 | Unknown keyword |
| S003 | Directive outside its allowed scope |
| S004 | Directive appears more times than allowed |
| S005 | Required directive or block missing |
| S006 | Task id has the wrong format |
| S007 | Duplicate task id |
| S008 | Block not closed, or END without a block |
| S009 | The file needs exactly one GLOBAL block |
| S010 | Directive arguments have the wrong form |
| G001 | DEPENDS names an unknown task |
| G002 | `${id.key}` names an unknown task |
| G003 | `${id.key}` names an OUTPUT the task does not declare |
| G004 | Dependency cycle |
| G005 | FILES overlap within a wave |
| P001 | Task PERMIT is not inside a GLOBAL PERMIT |
| P002 | FILES glob is not inside the write PERMIT |
| P003 | PERMIT or FILES glob is forbidden by a DENY |
| P004 | PERMIT spawn is not allowed |
| P005 | VERIFY command is not inside PERMIT run |
| F001 | FLOW step is not a TOOL role or a built-in step |
| F002 | SKIP names a step that is not in FLOW |
| F003 | SKIP of verify or report |
| F004 | TOOL role declared twice |
| T001 | Sentence has more than 20 words |
| T002 | Rejected word; use the approved word |
| T003 | Word that adds no meaning |
| T004 | Sentence starts with an -ing word |
| X001 | Unknown state |
| X002 | BECAUSE must go with completed_failure, and only with it |
| X003 | BY must go with blocked, and only with it |
| X004 | BY names a task that is not a failed or blocked dependency |
| X005 | Task started or finished before a dependency succeeded |

The linter reports structure errors (S) first. It runs the other checks only when the
structure is valid.

## Linter interface

    python3 ste_lint.py FILE                    # exit 0 valid, 1 errors, 2 usage or IO error
    python3 ste_lint.py FILE --waves            # wave N: id id …
    python3 ste_lint.py FILE --json             # {plan, global, tasks, waves}
    git diff --name-only A..B | python3 ste_lint.py FILE --audit TASK_ID
                                                # prints each path outside FILES; exit 1 if any
                                                # exit 2, errors on stderr: invalid FILE or unknown TASK_ID

`--json` gives each task its `branch`, `worktree`, `depends`, `wave`, `status`, and
verbatim `text`. It gives `plan.integration_branch`, `plan.integration_worktree`, and the
verbatim GLOBAL block as `global.text`.

## Example

The golden example is `example.ste` in this directory. `--waves` prints:

    wave 1: schema
    wave 2: endpoint
