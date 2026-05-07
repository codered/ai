# Agent Log Template

Use this file to create per-agent work logs on first run.
Create one file per agent at `.agents/[agent]/work-log.md`.

Append a new entry for every task action. **Never edit or delete previous entries.**

---

## Initial State

When first created, each work log contains only:

```markdown
# [Agent] Work Log
*Initialized [ISO date]*
```

Replace `[Agent]` with: PM / Dev / QA / Security / DevOps

---

## Entry Formats by Agent

### PM Entry

```markdown
## [Event] — [ISO date]
**Event:** Plan created / Phase N — [name] gate passed / Phase N — [name] gate failed
**Detail:** [What was decided, validated, or blocked. Include gate criteria status if a gate event.]
```

### Dev Entry

```markdown
## TASK-NNN — [Title] — [ISO date]
**Status:** in_review / done
**What was done:** [Brief summary of what was implemented]
**Tests written:** [List test names or describe what coverage was added]
**nasa-dod P0/P1 findings addressed:** [List findings fixed before handoff, or "None"]
**nasa-dod P2/P3 advisory findings:** [List advisory findings noted, or "None"]
```

Dev re-review entry (after addressing QA/Security findings):

```markdown
## TASK-NNN — [Title] — Re-review — [ISO date]
**Findings addressed:** [List TASK-NNN/F-NNN items resolved]
**Findings deferred:** [List TASK-NNN/F-NNN items deferred with override recorded]
**Status:** in_review
```

### QA Entry

```markdown
## TASK-NNN — [Title] — [ISO date]
**Findings raised:** N (N P0, N P1, N P2, N P3)
**Coverage:** [X% — above / below [threshold]% threshold]
**Summary:** [One sentence on overall test quality and correctness]
```

QA re-review entry:

```markdown
## TASK-NNN — [Title] — Re-review — [ISO date]
**Findings resolved:** [List F-NNN items confirmed fixed]
**Findings still open:** [List F-NNN items with explanation of why fix was insufficient]
**New findings raised:** [List any new findings from the fix, or "None"]
```

### Security Entry

```markdown
## TASK-NNN — [Title] — [ISO date]
**Findings raised:** N (N P0, N P1, N P2, N P3)
**Standards checked:** [e.g., OWASP Top 10, CERT, CWE, SOC2]
**Summary:** [One sentence on overall security posture]
```

Security re-review entry:

```markdown
## TASK-NNN — [Title] — Re-review — [ISO date]
**Findings resolved:** [List F-NNN items confirmed fixed at root cause]
**Findings still open:** [List F-NNN items — why fix was insufficient]
**New findings raised:** [List any new vulnerabilities introduced by fix, or "None"]
```

### DevOps Entry

```markdown
## [Feature Name] — Readiness Review — [ISO date]
**CI/CD:** Pass / Issues found — [brief description]
**Infrastructure:** Pass / Issues found — [brief description]
**Readiness Gate:** PASS / BLOCKED — [reason if blocked]
**Findings raised:** N (N P0, N P1, N P2, N P3)
**Deployment checklist:** [attached below or "See checklist in this entry"]

[Paste completed deployment readiness checklist here]
```
