# Memory Template

Use this file to create the two memory files on first run.

---

## Tier 1 — `.agents/memory/index.md`

**Always loaded first. Keep it small — one screen.**
Updated after every task action (status change, finding raised, blocker added).

```markdown
# Agent Team Index

**Project:** [one-line description]
**Feature:** [feature name — one line]
**Current Focus:** [Phase N — TASK-NNN]
**Last Updated:** [ISO timestamp]

## Agent Status
| Agent | Last Action | Status |
|-------|-------------|--------|
| pm | [description of last action] | ✅ / ⏳ / — |
| dev | [description of last action] | ✅ / ⏳ / — |
| qa | [description of last action] | ✅ / ⏳ / — |
| security | [description of last action] | ✅ / ⏳ / — |
| devops | [description of last action] | ✅ / ⏳ / — |

Status key: ✅ Complete · ⏳ In progress · — Not yet active

## Open Blockers
[One line per active blocker. Write "None." if no blockers.]
[PM writes here on gate failure. DevOps writes here on readiness blockers.]
[Format: [agent] — [one-line blocker description]]

## Open Findings (P0/P1 only)
[One line per unresolved critical or high finding. Write "None." if clear.]
[Format: TASK-NNN/F-NNN P0/Critical [source] — [one-line description]]

## Project Context (from init)
- **Language/Framework:** [value]
- **Environment:** [value]
- **Team:** solo / team
- **CI/CD:** [value]
- **Infra:** [value]
- **Test Framework:** [value]
- **Coverage Threshold:** [value]
- **Compliance:** [value or "None"]

## Key Files
- Plan: `.agents/pm/plan.md`
- Full state: `.agents/memory/project-state.md`
- Tasks: `.agents/pm/tasks/`
```

---

## Tier 2 — `.agents/memory/project-state.md`

**Full detail. Load only when needed:**
- Starting a new phase
- Resolving a P0/P1 finding
- A blocker is active
- An agent needs full project context

Updated after every task cycle and every phase gate.

```markdown
# Project State

**Last Updated:** [ISO timestamp]

## Project Context
- **Language/Framework:** [from init]
- **Environment:** [from init]
- **Team:** solo / team
- **Constraints:** [from init — deadlines, compliance, restrictions]
- **Tools/Libraries:** [from dev init questions]
- **Test Framework:** [from QA init questions]
- **Coverage Threshold:** [from QA init questions]
- **Security Testing:** [from security init questions]
- **Compliance Requirements:** [from security init questions]
- **CI/CD Platform:** [from devops init questions]
- **Infra Tooling:** [from devops init questions]
- **Environments:** [from devops init questions]

## Current Feature
- **Name:** [feature name]
- **Goal:** [one sentence]
- **Priority:** P0 / P1 / P2 / P3
- **Acceptance Criteria:**
  - [ ] [criterion]
  - [ ] [criterion]

## Phase Progress
| Phase | Status | Gate Criteria | Gate Met? |
|-------|--------|---------------|-----------|
| Phase 1 — [Name] | pending / in_progress / complete | [criteria] | ⏳ / ✅ |

## Full Task Summary
| ID | Title | Phase | Agent | Priority | Status |
|----|-------|-------|-------|----------|--------|
| TASK-001 | [title] | Phase 1 | dev | P0 | pending |

## All Findings
| ID | Source | Severity | Task | Status | Notes |
|----|--------|----------|------|--------|-------|

## Decisions Made
<!-- Append-only. Never delete entries. -->
<!-- Format: [ISO date] — [Decision and rationale] -->

## Overrides & Deferrals
<!-- Append-only. Never delete entries. -->
<!-- Format: [ISO timestamp] — TASK-NNN/F-NNN [Severity] deferred. Reason: [reason]. Revisit: [when]. -->
```

---

## Update Rules

| File | When to update |
|------|---------------|
| `index.md` | After every task action — status change, finding raised, blocker added/resolved |
| `project-state.md` | After every completed task cycle and every phase gate |
| Decisions Made log | Append only — when a significant decision is made |
| Overrides & Deferrals log | Append only — when a user overrides or defers a P0/P1 finding |
