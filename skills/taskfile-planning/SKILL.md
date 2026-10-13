---
name: taskfile-planning
description: Use when the user asks to write or run a Taskfile.ste, a line-oriented plan of LLM work with dependencies, permissions, and STE prose that an orchestrator runs as parallel waves of subagents in git worktrees. Triggers include "write a taskfile", "plan this as a Taskfile.ste", "taskfile-planning", and "run Taskfile.ste".
---

# Taskfile Planning

## Overview

A `Taskfile.ste` is a Dockerfile-style plan for LLM work. One GLOBAL block fixes the
environment, permissions, tools, and working method (FLOW). TASK blocks describe units
of work and their dependencies. Independent tasks run in parallel waves, each in its own
git worktree.

This skill has two modes:

- **Mode 1, Author:** write a Taskfile and make it pass the linter.
- **Mode 2, Run:** act as the orchestrator and run the Taskfile.

Mode 2 starts only on an explicit request. Never start it on your own.

**Files:**

- `references/format.md`: the grammar, every directive, the glob rules, and every error
  code. Load it before you write or fix a Taskfile.
- `references/ste_lint.py`: the linter. Standard library only.
- `references/example.ste`: a valid example.
- `skills/nfc/references/style-rules.md` (in this repository): the STE rules.

In the commands below, `LINT` means `python3 <this skill's directory>/references/ste_lint.py`.
Run every command from the repository root unless a step names a worktree.

## Mode 1: Author

**Triggers:** "write a taskfile", "plan this as a Taskfile.ste", "taskfile-planning".

1. **Globals.** Read the repo: lockfiles, CI config, and formatter config. Propose ENV,
   STACK, TOOL, and FLOW. Confirm them with the user in one message. In the same message,
   ask for what the repo does not show:
   - permissions, especially `network` and paths outside the repo;
   - `AGENTS max`;
   - the FLOW order.
2. **Tasks.** Make each task one unit that one subagent can finish and verify inside its
   own context. Add a dependency only when a task uses another task's result. Give each
   task the narrowest FILES.
3. **STE.** Write GOAL, STEP, RULE, and BECAUSE text under the `codered:nfc` strict rules.
   One instruction per STEP. Start each STEP with an imperative verb.
4. **Lint loop.** Run `LINT <file>` until it exits 0. Fix each error at its line.
   Never widen a GLOBAL permission to pass a check without asking the user.
5. **Present and stop.** Show the path, the `LINT <file> --waves` output, and one line
   per task. Then ask exactly: "Run this plan now, or later?"
   - On "later", stop. Give the command to run it: "run Taskfile.ste".
   - On "now", start Mode 2.

**Location:** write `Taskfile.ste` at the repo root. Use `plans/<name>.ste` when a
Taskfile already exists or the user wants several plans. Never overwrite an existing
file without asking.

## Mode 2: Run

**Start:** only on an explicit request, from the Mode 1 question or a later
"run <file>".

The orchestrator is the only writer of the Taskfile and the integration branch.
Subagents never edit either. The Taskfile's STATUS lines are the source of truth.

### Names

Take every name from `LINT <file> --json`. Do not parse the Taskfile yourself.

| Item | Value | JSON field |
|---|---|---|
| Base branch | The branch checked out when the run starts | — |
| Integration branch | `taskfile/<plan>/integration` | `plan.integration_branch` |
| Integration worktree | `<WORKTREES>/<plan>/integration` | `plan.integration_worktree` |
| Task branch | `taskfile/<plan>/tasks/<id>` | `tasks[].branch` |
| Task worktree | `<WORKTREES>/<plan>/tasks/<id>` | `tasks[].worktree` |

The Taskfile stays in the main working tree. Edit it there. Do not commit STATUS changes.
Create worktrees with `git worktree add`. Do not use a harness isolation feature that
picks its own paths or cleans up by itself, because the plan must control the names.

### Steps

1. **Validate.** Run `LINT <file> --json`. If it exits 1, show the errors and stop.
   When `tasklist` is true, mirror every task into your todo list.
2. **Prepare the workspace.**
   - Run `git status --porcelain`. Every line except the Taskfile must be absent.
     Otherwise stop and name the files.
   - Run `git check-ignore -q <WORKTREES>/`. If it exits non-zero, stop and tell the user
     to add `<WORKTREES>/` to `.gitignore`.
   - If the integration branch does not exist, create it from the base branch:
     `git branch <integration-branch> HEAD`.
   - If the integration worktree does not exist, run
     `git worktree add <integration-worktree> <integration-branch>`.
3. **Reset interrupted tasks.** For each task in `in_progress`:
   - If its worktree exists and `git -C <worktree> status --porcelain` is not empty,
     commit everything there as `<id>: uncommitted changes at interrupt`.
   - Run `git worktree remove --force <worktree>`.
   - Rename the branch: `git branch -m <branch> <branch>-attempt-<n>`. `n` is one more
     than the number of `<branch>-attempt-*` branches that exist.
   - Set the task's STATUS to `pending`. The old branch keeps its commits.
4. **For each wave, in order:**
   - Skip tasks at `completed_success`.
   - Write `STATUS blocked BY <dep>` on a task whose dependency is `completed_failure` or
     `blocked`.
   - For each remaining task, run
     `git worktree add -b <branch> <worktree> <integration-branch>`.
     Set its STATUS to `in_progress` and save the Taskfile.
   - Dispatch one subagent per task. Never run more than `agents_max` at once. Queue the
     rest, and start one each time a slot frees.
   - Each subagent prompt contains: its worktree path; `global.text`; the task's `text`
     with each `${id.key}` replaced by that dependency's OUTPUT value; and the FLOW
     contract below.
   - For each report, do "Audit and merge" below. Write `STATUS completed_success` or
     `STATUS completed_failure BECAUSE <reason>`.
   - After the wave, apply the COMPACT triggers (see "Compaction").
5. **Finish.** Run `git worktree remove <integration-worktree>`. Print one table row per
   task: id, final STATUS, BY chain, branch, and the worktree path of each failed task.
   Stop. There are no automatic retries. A re-run skips completed tasks. Never merge the
   integration branch into the user's branch. The user decides that.

### Audit and merge

Do these steps for each report, in the order that reports arrive. Merge one task at a
time. Let `INT` be the integration worktree and `WT` the task worktree.

1. **Save everything.** If `git -C WT status --porcelain` is not empty, run
   `git -C WT add -A` and commit as `<id>: uncommitted changes at report`.
2. **Attribute.** Run
   `git diff --name-only $(git merge-base <integration-branch> <branch>)..<branch> | LINT <file> --audit <id>`.
   If it exits 1, fail the task `BECAUSE changed files outside FILES`.
3. **Verify in isolation.** Run each VERIFY command in `WT`. Any non-zero exit fails the
   task. A report that claims success does not override this.
4. **Merge.** Save `PRE=$(git -C INT rev-parse HEAD)`. Run
   `git -C INT merge --no-ff -m "taskfile(<plan>): merge <id>" <branch>`.
   On a conflict, run `git -C INT merge --abort` and fail the task `BECAUSE merge conflict`.
5. **Verify after the merge.** Run each VERIFY command in `INT`. If one fails, run
   `git -C INT reset --hard $PRE` and fail the task `BECAUSE VERIFY failed after merge`.
   The task branch stays as it is.
6. **Clean up.** On success, run `git worktree remove WT` and keep the branch. On failure,
   keep both the worktree and the branch so the user can inspect them.

You own the integration branch, so step 5 can reset it. Never reset the base branch or a
task branch. Never run `git reset` in the main working tree: it holds the Taskfile's
uncommitted STATUS lines.

### Compaction

- `compact_after_wave`: compact between waves.
- `compact_when_context_pct`: compact when your context usage passes the threshold.

If you cannot start compaction yourself, stop at the end of the wave. Tell the user to
compact and then say "run <file>". The STATUS lines let the run continue. After any
compaction, read the Taskfile again before you continue.

### Heartbeats

Relay each heartbeat to the user in one line. Never write heartbeats to the Taskfile.

### FLOW contract (send it to each subagent verbatim)

- Work only in your worktree. Do not change the main working tree or another worktree.
- Commit your changes on your task branch before `report`. Do not merge, rebase, or push.
- Do the FLOW steps in order. Omit only the steps your SKIP lines name.
- Use only the TOOL named for each role.
- Stay inside PERMIT, DENY, and FILES.
- Do not start agents or subagents.
- Do not edit the Taskfile.
- Send a heartbeat after every n STEP lines when HEARTBEAT is set. If you have no way to
  send a message before you finish, put the heartbeats in your report.
- End with `report`, including on failure.
- If your context runs out, report `completed_failure BECAUSE context limit`.

## Errors

| Situation | Action |
|---|---|
| Invalid file | Mode 2 refuses to start and prints the lint errors |
| Subagent failure | The task becomes `completed_failure`; dependents become `blocked BY` it; independent tasks continue |
| False success report | The VERIFY check in step 3 fails the task |
| Changes outside FILES | `completed_failure BECAUSE changed files outside FILES` |
| Uncommitted changes | The orchestrator commits them on the task branch, then audits |
| VERIFY fails after the merge | The integration branch resets to `PRE`; `completed_failure BECAUSE VERIFY failed after merge` |
| Merge conflict | Abort the merge; `completed_failure BECAUSE merge conflict` |
| Dirty working tree, or WORKTREES not ignored | Mode 2 refuses to start and names the problem |
| Interrupted run | The old branch becomes `-attempt-<n>`; the task resets to `pending` |
| Subagent context exhausted | `completed_failure BECAUSE context limit`; the user splits the task |

## Red flags

| Thought | Reality |
|---|---|
| "The plan is valid, so I can start running it." | Mode 2 needs an explicit yes. Ask "Run this plan now, or later?" and stop. |
| "I will widen the GLOBAL PERMIT so the lint passes." | Ask the user first. |
| "The subagent says the tests pass." | Run VERIFY yourself, in the worktree and after the merge. |
| "Two tasks are independent, so I can start a third agent." | Never exceed `agents_max`. |
| "I will reset the main working tree to undo the merge." | Reset only the integration worktree. |
| "The integration branch looks good, so I will merge it into main." | The user decides that. |
