# Plan Directory Formats

    docs/plans/YYYY-MM-DD-<feature>/
      plan.md                machine-facing index
      plan_superpowers.md    human-facing plan
      taskkit.py             copied verbatim from the skill
      run.py                 copied verbatim from the skill
      tasks/task_NN_*.py     one apply+verify script per task

The `tasks/` scripts are the single source of truth. Both markdown files are
generated views. `run.py --status` probes every gate and rewrites the
checkboxes in `plan_superpowers.md`, so the human document reports measured
state rather than remembered state.

## plan.md — machine-facing

A seam map, then one table row per task. No prose beyond the seam map.

```markdown
# <Feature> — Plan Index

## Seams

| Seam | From | To | Verified by |
|---|---|---|---|
| client -> orders HTTP | client | svc/orders | scripts/smoke_retry.sh |

## Tasks

| # | Title | Kind | Tier | Touches | Crosses | Files | Script |
|---|---|---|---|---|---|---|---|
| 01 | Wire retry header end-to-end | scripted | T2 | client, svc/orders | client -> orders HTTP | client/http.py, svc/orders/handler.py | tasks/task_01_wire_seam.py |
```

## plan_superpowers.md — human-facing

Follows the superpowers writing-plans format: the plan header (Goal,
Architecture, Tech Stack, Spec), a Global Constraints section with
project-wide requirements copied verbatim, then per-task bite-sized steps.

Every task gets exactly one checkbox line carrying its script marker, which is
what `--status` rewrites:

```markdown
- [ ] **Task 01 — Wire retry header end-to-end** <!-- task_01_wire_seam.py -->
```

The marker comment must be the last thing on the line. Lines without a marker,
or whose marker names a script the runner did not run, are never touched.

## Running the plan

Tasks always run with `cwd = the target repo root`, never the plan directory.
This ensures that task scripts can use relative paths consistently, and that
edits land in the right place regardless of where the runner invoked `run.py`.

From the target repo root:

```bash
python3 docs/plans/YYYY-MM-DD-<feature>/run.py              # run tasks in order, stop at the first non-zero
python3 docs/plans/YYYY-MM-DD-<feature>/run.py --status     # probe every gate, report state, change nothing
```

From elsewhere (passing `--repo-root` to override the target directory):

```bash
python3 docs/plans/YYYY-MM-DD-<feature>/run.py --repo-root /path/to/repo
python3 docs/plans/YYYY-MM-DD-<feature>/run.py --status --repo-root /path/to/repo
```

### Programmatic invocation

```python
from run import run_task

# Run one task script. Returns (exit_code, report_dict).
# repo_root defaults to the current working directory if None.
exit_code, report = run_task(path, verify_only=False, repo_root=None)
```
