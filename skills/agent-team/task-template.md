# Task Template

Use this file when creating task files at `.agents/pm/tasks/TASK-NNN.md`.
Replace all placeholders with actual values — no field left blank.

Task IDs are sequential across all phases: TASK-001, TASK-002, TASK-003, etc.

---

```markdown
# TASK-NNN: [Title]

**Priority:** P0 / P1 / P2 / P3
**Phase:** [Phase name — e.g., Phase 1 — Foundation]
**Assigned:** dev / qa / security / devops
**Status:** pending
**Dependencies:** [TASK-NNN, TASK-NNN — or "None"]
**Created:** [ISO date]

## Description
[What needs to be done. Specific enough that the assigned agent can begin
without asking clarifying questions.]

## Acceptance Criteria
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

## Findings
| ID | Source | Severity | Description | Status |
|----|--------|----------|-------------|--------|

## History
| Date | Event |
|------|-------|
| [ISO date] | Task created by PM |
```

---

## Field Reference

### Status values
| Value | Meaning |
|-------|---------|
| `pending` | Not yet started |
| `in_progress` | Dev actively working |
| `in_review` | Dev complete — awaiting QA + Security review |
| `done` | All P0/P1 findings resolved or overridden; task closed |
| `deferred` | Deliberately postponed; reason recorded in History |

### Priority values
| Value | Label | Meaning |
|-------|-------|---------|
| `P0` | Critical | Blocks everything — must be done first in the phase |
| `P1` | High | Core functionality — required for feature completion |
| `P2` | Medium | Important but not blocking other tasks |
| `P3` | Low | Nice to have — deferrable if time-constrained |

### Finding ID format
- Sequential per task starting at F-001
- QA raises F-001, F-002, ... then Security continues the sequence
- When referenced in memory files, prefix with task ID: `TASK-003/F-001`

### Override format
Append to the History table when a user defers a P0/P1 finding:

```
| [ISO timestamp] | [OVERRIDE] TASK-NNN/F-NNN [Severity] deferred. Reason: [user reason]. Revisit: [next sprint / next feature / never]. |
```

Solo developers may self-override.
Team projects require 2+ peer approvals before recording the override.
