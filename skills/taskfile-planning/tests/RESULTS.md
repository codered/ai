# Taskfile Planning — Scenario Results

Scenarios: M1 (Author mode), M2 (Run mode, two rounds), W (audit without a
subagent). Fixture: `fixtures/make_scenario_repo.sh`. Scenario agents were
sonnet; Mode 2 task subagents were haiku; separate sonnet judges scored the
runs read-only. Run date: 2026-10-13.

The scratch repositories, logs, and judge notes of these runs were not retained.
The evidence in the tables below is the record.

## Fixture check

`ste_lint.py <scenario Taskfile> --waves` printed `wave 1: alpha beta delta`
and `wave 2: gamma epsilon`, as expected.

## M1 — Author mode

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Proposes ENV, STACK, TOOL, FLOW from repo files; asks about permissions, AGENTS max, FLOW order | PASS | Message 1 proposed ENV os=linux python=3.12, STACK python pytest ruff, TOOL edit/fmt, FLOW and PERMITs from `pyproject.toml`. It asked three questions: network permission, AGENTS max, FLOW order. |
| 2 | Taskfile lints with exit 0; transcript shows the lint loop | PASS (weak on the loop) | Lint exit 0; `--waves`: subtract / multiply / readme. The log shows one clean lint pass and no failing iteration. |
| 3 | README task depends on code tasks only if it uses their results; narrow FILES | PASS | `readme` depends on `multiply` and uses `${subtract.signature}` and `${multiply.signature}`; FILES `README.md`. `multiply` depends on `subtract` because both write `src/calc.py` and `tests/test_calc.py` (lint G005). The old wording did not cover this case. |
| 4 | Ends with exactly "Run this plan now, or later?"; no subagent, no worktree | PASS (minor blemish) | The exact line was present, followed by one parenthetical line. `git worktree list` and `git branch` showed `main` only. |

Wording changes from M1: dependency allowed when two tasks change the same
file; the question must be the last line of the message (Step 6).

## M2 round 1 — Run mode

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | At most 2 subagents at once | PASS (weak evidence) | Log order: alpha+beta, alpha+delta, delta+gamma. `delta` queued until `beta` finished. No timestamps. |
| 2 | Final STATUS lines; lint exit 0 | PASS | alpha, beta, gamma `completed_success`; delta `completed_failure BECAUSE VERIFY failed`; epsilon `blocked BY delta`; lint exit 0. |
| 3 | Branches | PASS | integration plus tasks/{alpha,beta,delta,gamma}; none for epsilon. |
| 4 | Exactly 3 merge commits | PASS | `taskfile(scenario): merge gamma`, `merge alpha`, `merge beta`. |
| 5 | `src/gamma.txt` contains `alpha` | PASS | `git show taskfile/scenario/integration:src/gamma.txt` printed `alpha`. |
| 6 | Worktrees | PASS | Only main and `.worktrees/scenario/tasks/delta`. |
| 7 | `main` untouched | PASS | `main` at "Scenario start"; no merge into it. |

**Audit incident (process failure, not a criterion).** The orchestrator
merged `gamma` after `--audit` exited 1. Cause: it left `beta` at
`in_progress`, so the Taskfile failed lint (X005). `--audit` printed lint
errors on stdout with exit 1, the same signal as paths outside FILES. Near
misses: a worktree and `in_progress` were written for queued `delta` and then
reverted; `gamma` (wave 2) started before `delta` (wave 1) had a final STATUS;
`delta`'s failure was written before its report arrived.

## Step 6 changes (from the incident and near misses)

- `ste_lint.py`: in `--audit` mode, lint errors go to stderr with exit 2;
  `--audit ""` is handled with `is not None`. New test
  `test_invalid_plan_exits_2_on_stderr` (75 tests).
- `format.md`: documents audit exit 2.
- `SKILL.md`: dependency allowed when two tasks must change the same file; the
  run question is the last line; queued tasks get no worktree or `in_progress`
  until they start; audit only after a report; write STATUS, save, and lint
  (exit 0) before the next audit; next wave only after every task in the wave
  has a final STATUS; Retry commits a dirty worktree first; Attribute handles
  exit 0, 1, and 2 explicitly; Errors table row "Audit exits 2".

`python3 -m unittest discover -s skills/taskfile-planning/tests`: Ran 75 tests, OK.

## M2 round 2 — Run mode (fresh repository, revised SKILL.md)

| # | Criterion / point | Result | Evidence |
|---|---|---|---|
| 1 | At most 2 subagents; one wave-1 task queues | PASS (log-based) | alpha and beta dispatched first; `delta` created and dispatched only after `beta`'s merge and cleanup. |
| 2 | Final STATUS lines; lint exit 0 | PASS | Same five states as round 1; lint exit 0. |
| 3 | Branches | PASS | integration plus tasks/{alpha,beta,delta,gamma}. |
| 4 | Exactly 3 merge commits | PASS | merge gamma, alpha, beta. |
| 5 | `src/gamma.txt` contains `alpha` | PASS | `alpha`. |
| 6 | Worktrees | PASS | Only main and delta's. |
| 7 | `main` untouched | PASS | `Scenario start` only; status shows `?? Taskfile.ste`. |
| A | Audit exit 0 before every merge; no audit before the report | PASS (log-based) | Per task: report, status, audit exit 0, VERIFY, rev-parse, merge. `delta`: audit 0, VERIFY failed, no merge. |
| B | Lint exit 0 after each STATUS write | PASS | Seen after every STATUS write and `in_progress` write. |
| C | No wave-2 task starts before wave 1 is final | PASS | `delta` final, `epsilon` blocked, then `gamma` started. |
| D | No worktree or `in_progress` for a queued task | PASS | `delta`'s worktree and `in_progress` appear only after the slot freed. |

Caveat: the log is self-reported. PASS results rest on log order and on the
directly checked repository state. Scenario W exercises the audit exit-1 path;
the unit test exercises the exit-2 path.

## Scenario W — audit without a subagent

Run from the root of a fresh scenario repository. Commands from `SKILL.md`:
"Prepare the workspace", `git worktree add -b` (step 4), "Attribute", and
"Reset interrupted tasks".

| Expectation | Result | Evidence |
|---|---|---|
| Attribute prints `README.md` and exits 1 | PASS | The task commit changed `src/alpha.txt` and `README.md`. Output `README.md`, exit 1. |
| Reset renames the branch to `taskfile/scenario/tasks/alpha-attempt-1` | PASS | `git branch --list 'taskfile/*'` printed the integration branch and `taskfile/scenario/tasks/alpha-attempt-1`. Only the integration worktree remained. |

## Known residuals

- The M1 transcript shows a single lint pass, so the lint loop is not shown
  failing and recovering.
- M2 subagent concurrency and ordering rest on self-reported logs.
- A judge suggested stating when to write `blocked BY` ("as soon as that
  dependency reaches that state, then lint"). No FAIL; not changed.
- Scenario agents were sonnet and task subagents haiku. Other models are
  untested.
