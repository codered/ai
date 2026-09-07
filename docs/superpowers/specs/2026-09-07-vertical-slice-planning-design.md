# Vertical Slice Planning — Design

**Date:** 2026-09-07
**Status:** Approved for planning
**Skill name:** `vertical-slice-planning`
**Location:** `skills/vertical-slice-planning/`

## Problem

Implementation plans for multi-component work are usually written as horizontal
layers: build the backend, then the client, then wire them together. Every
integration defect is discovered at the end, at maximum cost, and the plan gives
no honest signal of progress until the final step.

Two failures compound this:

1. **Gates are prose.** "Verify the endpoint works" is a sentence, not a check.
   Nothing forces it to actually run, so it doesn't.
2. **Edits are described, not executed.** The plan says what to change; whether
   the change landed correctly is rediscovered by hand, later.

## Solution

A planning skill that emits an executable plan: an ordered set of vertical
slices, each one a Python script that both applies its change and proves it, and
each one exercising every component it touches rather than deferring integration.

The skill is **plan-only**. It produces the artifact and stops. Execution is a
separate act by a human or another agent.

## Scope

**In scope:** producing the plan directory; the `taskkit.py` edit engine that
generated scripts depend on; the formats of both plan documents.

**Out of scope:** executing plans, driving subagents, CI integration, resuming a
partially-executed plan beyond what `run.py --status` reports.

## Artifact

The skill emits one directory:

```
docs/plans/YYYY-MM-DD-<feature>/
  plan.md                  machine-facing index
  plan_superpowers.md      human-facing plan, superpowers format
  taskkit.py               edit engine, copied verbatim from the skill
  tasks/task_01_*.py …     one apply+verify script per task
  run.py                   ordered runner, --status probe
```

**The `tasks/` scripts are the single source of truth.** Both markdown files are
generated views of them. `run.py --status` probes every task's `verify()` and
rewrites the checkboxes in `plan_superpowers.md`, so the human document reports
measured state rather than remembered state.

### plan.md (machine-facing index)

A seam map plus one table row per task: id, title, kind (`scripted` | `manual`),
gate tier, components touched, seams crossed, files touched, script path. No
prose beyond the seam map. This is the file an executing agent reads to decide
what runs next and what a failure means.

### plan_superpowers.md (human-facing)

Follows the superpowers writing-plans format: the plan header (Goal,
Architecture, Tech Stack, Spec path), a Global Constraints section carrying
project-wide requirements verbatim, then per-task bite-sized `- [ ]` steps and
each task's gate criteria in prose. This is the review artifact — what a human
reads in a PR to judge whether the plan is right.

## Task Scripts

One file per task. Complete and runnable at plan time — a task's `verify()` runs
today and fails today, before its `apply()` has ever run.

```python
"""Task 03 — thread retry config through client → service seam."""
from taskkit import Editor, gate, ManualTask

KIND   = "scripted"
TIER   = "T2"
TOUCHES = ["client", "svc/orders"]
CROSSES = ["client→orders HTTP"]

def apply():
    with Editor("client/http.py") as ed:
        n = ed.locate("    return self._send(req)")
        ed.swap(n, ["    return self._send(req, retries=self.retries)"])

def verify():
    gate.structural(...)      # T0 — the edit is present
    gate.component(...)       # T1 — touched components' tests
    gate.crossing(...)        # T2 — real call through the seam

if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
```

`gate.run` makes the script idempotent: it probes `verify()` first, skips
`apply()` if the change is already present, and always runs the full gate.

### Exit contract

Uniform across every task; `run.py` depends on it.

| Code | Meaning |
|---|---|
| `0` | Applied (or already applied) and all gates pass |
| `1` | Gate failed — the work is wrong |
| `3` | Drift — anchor gone; halt and replan, do not guess |
| `4` | Manual task awaiting a human or agent edit |

`run.py` runs tasks in order, stops at the first non-zero exit, prints that
task's report JSON (`backend`, per-tier results, timing), and never advances
past a red gate.

## The Edit Engine (`taskkit.py`)

hashline is **mandatory** for editing existing files. Generated code may not use
`grep`, `sed`, string-replace tools, or `open(...).write()`; all edits go through
`Editor`, which shells out to the `hashline` CLI (developed against 0.9.1:
`read --json`, `patch --dry-run --json`). No MCP dependency — the artifact runs
as plain Python.

`Editor.locate(expected_line)` replaces search: it matches against hashline's own
read output and returns the `line:hash` anchor, so targeting and drift-checking
are a single act. `locate_block(...)` wraps `find-block` for whole-function
replacement. Anchors are computed at **run** time and never baked in at plan
time — this is what lets a task-7 script written today survive tasks 1–6 landing
tomorrow. The context manager emits one patch per file, addressing original line
numbers, and inspects the returned text for a leading `Error:` — hashline
reports rejection as a successful call returning error text, so a rejection must
never be read as success.

### Fallback ladder

Each step is recorded in the task's report.

1. hashline `patch --dry-run`, then apply.
2. hashline **rejects on drift** (`Error: ... content changed since last read`)
   → exit `3`, halt, replan. This is a true signal, not a reason to fall back.
3. hashline **unavailable or malfunctioning** (binary missing, non-`Error`
   crash, unsupported file) → AST fallback (`ast`/`libcst` for Python,
   node-anchored regex otherwise) then atomic write. Prints
   `WARN: fallback backend used` and stamps `backend: fallback` in the report.

The distinction between 2 and 3 is load-bearing: **drift halts, tool failure
degrades.** Collapsing them would let a genuine conflict be silently overwritten
by the fallback path.

## Planning Algorithm

The six steps the skill instructs the agent to perform.

**1. Seam map first.** Before any task exists, enumerate components and the
*seams* between them (HTTP route, queue topic, DB table, module import). Seams,
not components, drive ordering.

**2. Slice ordering.** Tasks are ordered so each is a thin path through every
component it touches. Task 1 of a multi-component feature wires the seam
end-to-end with the most trivial payload that can be verified — a hardcoded
response, one field, one row. Later tasks thicken it. A task that adds capability
to exactly one component without exercising a seam is permitted only when no seam
is yet in scope.

**3. Gate tiers.** Each task's `verify()` composes these; the tier is declared in
`plan.md`.

| Tier | Runs | Required when |
|---|---|---|
| T0 structural | asserts the edit landed (anchor re-read / AST) | always |
| T1 component | the touched component's own tests | always |
| T2 crossing | real end-to-end call through the seam this task wired | task touches ≥2 components |

T2 is neither optional nor deferrable — it is the property the whole skill
exists to buy. If a T2 gate cannot be run in the target environment, the *plan*
is wrong: the skill says so at plan time rather than emitting a task that cannot
prove itself.

**4. Scripted vs manual**, decided per task in this order:

- New file → **scripted**, full content embedded in `apply()`.
- Edit whose target set and result are determinable now → **scripted** via `Editor`.
- Otherwise (design judgement, ambiguous refactor) → **manual**: prose steps in
  `plan_superpowers.md`, `apply()` raises `ManualTask` carrying those
  instructions, exit `4`. **`verify()` is still fully written and runnable.**

The gate never goes manual. A manual task is manual in its edit, never in its
proof.

**5. Emit the directory** — scripts first, then both markdown views generated
from them.

**6. Self-check before handing over.** Every `verify()` is executed as written:
each must fail cleanly (exit `1`) rather than error, confirming the gates are
real. Any task whose gate errors is a defect in the plan.

## Skill Structure

```
skills/vertical-slice-planning/
  SKILL.md              trigger, the six steps, red-flags table
  references/
    taskkit.py          shipped verbatim; copied into each plan directory
    task_template.py    canonical scripted + manual task shapes
    plan_formats.md     plan.md schema, plan_superpowers.md header rules
    hashline_rules.md   the ladder, exit codes, banned-tool list
```

`taskkit.py` ships with the skill rather than being regenerated per plan: the
edit engine is tested once, and every plan inherits a fix.

## Testing

**`taskkit.py`** gets real pytest coverage against a scratch repository:

- clean apply lands the edit
- re-apply is a no-op that still passes (idempotence)
- file drifted under the script → exit `3`, no write performed
- hashline binary absent → fallback backend used, `WARN` emitted, edit lands
- hashline returns `Error:` text → treated as failure, never as success

**End-to-end:** a fixture repository with two components and one seam is planned
by the skill and executed to green, proving the emitted directory runs.

## Decisions Made

- Standalone skill in `codered/ai`; no dependency on the superpowers plugin.
- Plan-only; no execution, no subagent orchestration.
- One script per task combining apply and verify, idempotent.
- Scripts fully written and runnable at plan time, with runtime anchor
  resolution as the defence against drift.
- Tiered gates with mandatory crossing checks.
- hashline mandatory, with a fallback that is loud and recorded.
