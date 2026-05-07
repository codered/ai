# Agent Team Skill — Design Spec
**Date:** 2026-05-06
**Status:** Approved

---

## Overview

A standalone, agent-agnostic skill that spins up a five-role agent team (PM, Dev, QA, Security, DevOps) for any project or feature. Works with any LLM-based coding assistant that can read markdown. Each agent has a distinct persona, scope, and set of responsibilities. They collaborate through a shared memory system and a rolling pipeline that keeps work moving without bottlenecks.

---

## File Structure

```
skills/agent-team/
├── README.md                  # Orchestrator — triggers, init flow, pipeline logic
├── pm.md                      # PM agent instructions
├── dev.md                     # Dev agent instructions
├── qa.md                      # QA agent instructions
├── security.md                # Security agent instructions
├── devops.md                  # DevOps agent instructions
├── task-template.md           # Canonical task file format
├── memory-template.md         # project-state.md format
└── agent-log-template.md      # Per-agent work-log format
```

**Created in the target repo on first run:**

```
.agents/
├── memory/
│   ├── index.md               # Lightweight summary — always loaded first
│   └── project-state.md       # Full detail — loaded only when needed
├── pm/
│   ├── plan.md                # Feature plan with phases and gate criteria
│   └── tasks/
│       ├── TASK-001.md
│       ├── TASK-002.md
│       └── ...
├── dev/
│   └── work-log.md
├── qa/
│   └── work-log.md
├── security/
│   └── work-log.md
└── devops/
    └── work-log.md
```

---

## Trigger Phrases

| Phrase | Behavior |
|--------|----------|
| `init agent team` | First-time setup — creates `.agents/`, runs all upfront questions, begins planning |
| `agent team` | Auto-detects context — resumes from `memory/index.md` if team exists, inits if not |
| `agent team status` | Prints current `memory/index.md` without starting any work |

Auto-activation: when a new feature or project is mentioned and `.agents/` exists, the agent loads `memory/index.md` and resumes from the appropriate point in the pipeline.

---

## Initialization Flow

```
Trigger received
        │
        ▼
.agents/ exists?
  Yes ──► Load memory/index.md → resume from current pipeline position
  No  ──► First-time setup begins
        │
        ▼
PM asks project-wide questions (one at a time):
  1. What is the project/feature being built?
  2. What is the primary language and framework?
  3. What is the target environment? (cloud, on-prem, containerized, serverless)
  4. Solo developer or team? (affects override rules)
  5. Any hard constraints? (deadlines, compliance requirements, tech restrictions)
        │
        ▼
Dev asks project-wide questions:
  1. What tools and libraries are preferred?
  2. Are there coding style guides, linters, or formatters to follow?
        │
        ▼
QA asks project-wide questions:
  1. What test frameworks should be used?
  2. What is the minimum acceptable test coverage?
        │
        ▼
Security asks project-wide questions:
  1. What type of security testing is required? (SAST, DAST, dependency scanning)
  2. Are there compliance requirements? (SOC2, HIPAA, PCI-DSS, GDPR, etc.)
        │
        ▼
DevOps asks project-wide questions:
  1. What is the CI/CD platform? (GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.)
  2. What is the infra tooling? (Terraform, Pulumi, Docker, Kubernetes, etc.)
  3. What environments exist? (dev, staging, prod — and their differences)
        │
        ▼
All answers written to memory/index.md and memory/project-state.md
.agents/ directory scaffold created
PM begins feature planning
```

---

## PM Agent Behavior

```
PM receives feature request
        │
        ▼
Reads memory/index.md first
        │
        ▼
Asks feature-specific questions (one at a time):
  1. What is the goal of this feature? What problem does it solve?
  2. Who are the users or systems affected?
  3. What are the acceptance criteria or definition of done?
  4. Are there dependencies on other features or services?
  5. What is the priority of this feature? (P0–P3)
        │
        ▼
Creates .agents/pm/plan.md:
  - Feature summary and goal
  - Acceptance criteria
  - Risks and dependencies
  - Phases (ordered) with gate criteria
  - Task list per phase with priorities and agent assignments
        │
        ▼
Creates one .agents/pm/tasks/TASK-NNN.md per task
        │
        ▼
Updates memory/index.md and memory/project-state.md
        │
        ▼
Signals Dev — first phase is ready
```

### Phase Structure

Tasks are grouped into phases. All tasks in a phase must complete before the next phase begins. Tasks within a phase can run concurrently where dependencies allow.

```
Phase 1 — Foundation         (gate: all P0 tasks complete)
  TASK-001  P0  dev
  TASK-002  P1  dev

Phase 2 — Core Feature       (gate: acceptance criteria met)
  TASK-003  P1  dev
  TASK-004  P1  qa

Phase 3 — Hardening          (gate: no open P0/P1 findings)
  TASK-005  P1  security
  TASK-006  P2  devops

Phase 4 — Delivery           (gate: readiness checklist signed off)
  TASK-007  P1  devops
```

### Task File Format

Each `TASK-NNN.md` contains:
```markdown
# TASK-NNN: [Title]

**Priority:** P0 / P1 / P2 / P3
**Phase:** [Phase name]
**Assigned:** dev / qa / security / devops
**Status:** pending | in_progress | in_review | done | deferred
**Dependencies:** TASK-NNN, TASK-NNN

## Description
[What needs to be done]

## Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2

## Findings
| ID | Source | Severity | Description | Status |
|----|--------|----------|-------------|--------|

## History
[Dated log of status changes, decisions, overrides]
```

### Task Priorities

| Priority | Label | Meaning |
|----------|-------|---------|
| P0 | Critical | Blocks everything — must be done first |
| P1 | High | Core functionality — required for completion |
| P2 | Medium | Important but not blocking |
| P3 | Low | Nice to have — deferrable |

---

## Rolling Pipeline

> **Single-agent note:** This pipeline is executed by one agent adopting each role in turn. "QA and Security review in parallel" means the agent completes the QA review pass, then the Security review pass, before signaling Dev to check findings. The agent switches roles explicitly — it does not run true concurrent threads.

```
PM signals phase ready
        │
        ▼
Dev picks up first pending task in phase
Dev asks task-specific questions if needed (lazy — only if unclear)
Dev implements task
Dev updates .agents/dev/work-log.md
Dev marks task: in_review
        │
        ▼
Agent adopts QA role:
Reviews completed task
Updates qa/work-log.md
Produces findings with severity
Adds to TASK-NNN.md findings table
        │
        ▼
Agent adopts Security role:
Reviews completed task
Updates security/work-log.md
Produces findings with severity
Adds to TASK-NNN.md findings table
        │
        ▼
        Agent adopts Dev role — picks up NEXT task (does not wait)
                           │
                           ▼ (when both QA + Security complete)
        Dev checks findings on previous task
                           │
                           ▼
        P0/Critical or P1/High findings?
  Yes ──► Dev addresses findings
          QA + Security re-review
          Repeat until clean or override
  No  ──► Task marked: done
          memory/index.md and project-state.md updated
                           │
                           ▼
        User override on P0/P1 findings:
        "I want to defer this." ──► noted in TASK-NNN.md + memory
                                     tagged: deferred — [reason] — [date]
                           │
                           ▼
        All tasks in phase complete?
  Yes ──► PM validates phase gate
          Updates plan.md gate status
          Signals next phase
  No  ──► Dev continues next task in phase
                           │
                           ▼
        All phases complete?
  Yes ──► DevOps agent activates
```

### Finding ID Format

Findings are assigned sequential IDs per task: `F-001`, `F-002`, etc., scoped to the task file. When referenced in memory files, they are prefixed with the task ID: `TASK-003/F-001`.

### Severity / Handback Rules

| Severity | Label | Action |
|----------|-------|--------|
| P0 | Critical | Blocks task close — Dev must fix; user may override with recorded reason |
| P1 | High | Blocks task close — Dev must fix; user may override with recorded reason |
| P2 | Medium | Advisory — noted in task file, does not block |
| P3 | Low | Informational — noted in task file, no action required |

Override format recorded in task file:
```
[OVERRIDE] 2026-05-06T14:32:00Z — F-007 P1/High deferred
Reason: [user-provided reason]
Revisit: [next sprint / next feature / never]
```

---

## DevOps Agent Behavior

```
All phases complete + PM confirms delivery phase gate
        │
        ▼
DevOps reads memory/index.md + all task files
        │
        ▼
Asks task-specific questions if needed (lazy):
  - Has infra changed from what was configured at init?
  - Are there new environment variables or secrets to manage?
  - Are there migration steps required? (DB, config, feature flags)
        │
        ▼
Three parallel workstreams:

CI/CD                    Infrastructure            Readiness Gate
─────────────────        ──────────────────        ────────────────────
Review/update            Review/update             Read all findings
pipeline configs         infra configs             across all agents
(Actions, GitLab CI)     (Terraform, k8s,          and all task files
                          Docker Compose)
Ensure build, test,      Validate env parity       Produce deployment
security scan steps      across dev/staging/prod   checklist:
are wired in                                        □ All tests passing?
                         Document rollback          □ P0/P1 findings clear?
                         procedure                  □ Infra ready?
                                                    □ Rollback plan exists?
                                                    □ Migrations documented?
        │
        ▼
Any P0/P1 blockers in readiness checklist?
  Yes ──► Hands back to relevant agent (dev / security / qa)
  No  ──► Feature marked: READY TO SHIP
        │
        ▼
Writes deployment checklist to .agents/devops/work-log.md
Updates memory/index.md with final status: READY TO SHIP
```

---

## Memory System

### Tier 1 — `memory/index.md` (always loaded first, kept small)

```markdown
# Agent Team Index

**Project:** [one line]
**Feature:** [one line]
**Current Focus:** [active phase — active task]

## Agent Status
| Agent | Last Action | Status |
|-------|-------------|--------|
| pm | Closed Phase 1 gate | ✅ |
| dev | Working TASK-004 | ⏳ |
| qa | Reviewing TASK-003 | ⏳ |
| security | Idle | — |
| devops | Waiting | — |

## Open Blockers
[One line per active blocker — empty if none]

## Open Findings (P0/P1 only)
[One line per critical/high unresolved finding — empty if none]

## Key Files
- Plan: .agents/pm/plan.md
- Full state: .agents/memory/project-state.md
- Tasks: .agents/pm/tasks/
```

### Tier 2 — `memory/project-state.md` (full detail, loaded only when needed)

Loaded when: starting a new phase, resolving a finding, a blocker exists, or an agent needs full context.

```markdown
# Project State

## Project Context
[From init — language, framework, environment, team size, constraints]

## Current Feature
[Feature name, goal, acceptance criteria]

## Phase Progress
| Phase | Status | Gate Criteria | Gate Met? |
|-------|--------|---------------|-----------|

## Full Task Summary
| ID | Title | Agent | Priority | Status |
|----|-------|-------|----------|--------|

## All Findings
| ID | Source | Severity | Task | Status | Notes |
|----|--------|----------|------|--------|-------|

## Decisions Made
[Append-only dated log — nothing deleted]

## Overrides & Deferrals
[Append-only log of all user overrides with reason and revisit date]
```

### Update Rules
- `index.md` — updated after every task action (status change, finding raised, blocker added)
- `project-state.md` — updated after every task cycle and every phase gate
- Decisions Made and Overrides logs are append-only — nothing is ever deleted

---

## Agent Personas & Tone

**PM** — Organized, thorough, asks sharp questions. Never starts work without clear acceptance criteria. Owns the plan and defends it.
> "Before I create the plan, I need to understand the definition of done. What does success look like for this feature?"

**Dev** — Pragmatic, direct, focused on shipping clean working code. Asks about tooling preferences upfront and doesn't re-ask. Acknowledges findings without defensiveness.
> "TASK-003 complete. Two findings from QA — addressing the input validation issue now, deferring the coverage gap to TASK-005 with PM sign-off."

**QA** — Methodical, thorough, never skips edge cases. Asks about frameworks once and owns the test strategy from that point.
> "Coverage on the auth module is at 61% — below the agreed threshold. Raising F-007 as P1/High. Dev needs to address before this task closes."

**Security** — Precise, serious, non-negotiable on critical findings. References specific standards (OWASP, CVE, CERT) when flagging issues.
> "F-008: SQL injection vector at user-input.ts:47. OWASP A03:2021. P0/Critical — this blocks merge. Three remediation options below."

**DevOps** — Systems thinker, focused on reliability and repeatability. Asks about environments and doesn't assume.
> "No rollback procedure documented for the DB migration in TASK-006. Raising as P1/High before marking this feature ready to ship."

---

## Key Design Decisions

- **Agent-agnostic** — plain markdown, works with any LLM-based coding assistant
- **Two-tier memory** — `index.md` stays small for context efficiency; `project-state.md` holds full detail
- **Rolling pipeline** — Dev never blocks on QA/Security review; findings are addressed asynchronously
- **Phase gates** — PM validates completion before next phase begins; prevents work proceeding on a broken foundation
- **Override audit trail** — every deferred or overridden P0/P1 finding is recorded with reason, timestamp, and revisit date; nothing is silently skipped
- **Lazy task questions** — agents only ask task-specific questions when a task is ambiguous; project-wide questions asked once at init
