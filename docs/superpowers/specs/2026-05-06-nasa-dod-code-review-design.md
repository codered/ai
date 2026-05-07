# NASA/DOD Code Review Skill — Design Spec
**Date:** 2026-05-06
**Status:** Approved

---

## Overview

A standalone, agent-agnostic skill that reviews code against NASA and DOD best practices. Installable by anyone into any AI coding assistant (Claude, Copilot, Cursor, Gemini, etc.) that can read markdown context files. Categorizes findings by severity (P0–P3), enforces PR gate logic, manages CODEOWNERS, and outputs findings to both terminal and a saved report file. Used during active development and PR review.

---

## Distribution

Published as a standalone GitHub repository. Users install it one of two ways:

**Global install** (works across all repos):
```bash
git clone https://github.com/<org>/nasa-dod-code-review ~/.agent-skills/nasa-dod-code-review
```

**Per-repo install** (lives alongside the code):
```bash
git clone https://github.com/<org>/nasa-dod-code-review .agent-skills/nasa-dod-code-review
```

Users then reference the skill in their agent's context/instructions file (e.g., `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `copilot-instructions.md`):
```
When asked to review code, load and follow .agent-skills/nasa-dod-code-review/README.md
```

---

## File Structure

```
nasa-dod-code-review/
├── README.md                 # Entry point — full skill instructions the agent follows
├── standards-sources.md      # Authoritative URLs for NASA/DOD/language standards
├── reviewer-prompt.md        # Focused analysis prompt for the code review pass
├── severity-guide.md         # P0–P3 definitions with concrete examples per level
├── codeowners-template.md    # CODEOWNERS setup instructions + template
└── report-template.md        # Findings report structure (file output)
```

`README.md` is the orchestrator. It defines the full flow, references companion files by name, and is the only file an agent needs to load first — companion files are pulled in as needed during execution.

---

## Activation

### Trigger Phrases
The skill README documents these canonical trigger phrases that any user can say:
- `"nasa-dod review"` — runs in the appropriate mode (dev or PR) based on context
- `"nasa-dod dev review"` — explicitly forces full codebase scan
- `"nasa-dod pr review"` — explicitly forces PR/diff mode

### Agent Setup
Users add one line to their agent's context file:
```
When you see "nasa-dod review", load and follow .agent-skills/nasa-dod-code-review/README.md
```
The README explains the trigger phrases, both installation paths, and what the agent should do when activated.

---

## Skill Flow

```
Trigger phrase received
        │
        ▼
.github/CODEOWNERS exists?
  No ──► First-run setup (see CODEOWNERS section)
        │
        ▼
Detect: language(s), solo/team (from config), PR vs dev context
        │
        ▼
Load standards-sources.md → fetch authoritative standards — cache in session
        │
        ▼
PR mode?
  Yes ──► Recent full scan on target branch? (check last_full_scan in config)
              No ──► Prompt user to run full scan first before proceeding
              Yes ──► Analyze diff files only
  No (dev mode) ──► Analyze full codebase
        │
        ▼
Load reviewer-prompt.md → perform analysis pass
Generate findings (P0/Critical → P3/Advisory)
Tag approvers on P0 and P1 findings (via GitHub PR comment: @username)
        │
        ▼
P0 found?
  Yes ──► BLOCK + assert reasoning for each issue
              Solo dev? ──► Yes: allow override, record in report with timestamp
              Team? ──► Require 2+ peer approvals to override
        │
        ▼
Output findings to terminal
Write reports/code-review-YYYY-MM-DD.md to repo
Update last_full_scan in .github/nasa-dod-review-config.json (full scans only)
```

---

## Severity Scale

| Level | Label | Meaning |
|-------|-------|---------|
| P0 | Critical | Blocks merge. Safety, reliability, or security risk. Non-negotiable. |
| P1 | Major | Must be addressed soon. Significant risk or standards violation. |
| P2 | Minor | Should be fixed. Code quality, maintainability concern. |
| P3 | Advisory | Informational. Best-practice nudge, no action required. |

Full definitions and examples per level live in `severity-guide.md`.

---

## Findings Report Structure

### Report File
Saved to: `reports/code-review-YYYY-MM-DD.md` inside the repo being reviewed.
Also output in full to terminal/chat.

### Report Sections
1. **Summary header** — date, branch, scan type (full/diff), total counts per severity, gate status (BLOCKED / PASSED)
2. **What looks good** — brief acknowledgment of solid patterns found (sets tone)
3. **P0/Critical** — all blocking issues with full assertion language
4. **P1/Major** — significant issues requiring attention
5. **P2/Minor** — style/structure improvements
6. **P3/Advisory** — informational, best-practice nudges
7. **Override log** — any approvals or solo-dev overrides with timestamp + reason

### Finding Entry Format

```markdown
## [P0/Critical] Unbounded loop with no termination guarantee
**File:** src/controllers/flight.c:142
**Rule:** NASA Power of Ten — Rule 2 (bound all loops)
**Language:** C
**Why this must be fixed:** Unbounded loops in safety-critical systems can cause
indefinite blocking, watchdog timeouts, or system hangs with no recovery path.

### Fix Options

**Option 1 — Fixed iteration cap** *(recommended)*
Add a compile-time constant as the loop upper bound.
- ✅ Simple, auditable, zero runtime overhead
- ❌ Requires knowing max iterations at design time

```c
#define MAX_ITERATIONS 1000
for (int i = 0; i < MAX_ITERATIONS; i++) {
    if (done) break;
    process();
}
```

**Option 2 — Timeout-guarded loop**
Pair loop with a watchdog timer that forces exit after N ms.
- ✅ Works when iteration count is truly unknown
- ❌ Adds timing dependency; harder to test deterministically

```c
uint32_t start = get_time_ms();
while (!done) {
    if ((get_time_ms() - start) > TIMEOUT_MS) { handle_timeout(); break; }
    process();
}
```

**Option 3 — Recursive rewrite with depth limit**
Replace loop with bounded recursion and a depth counter.
- ✅ Formally provable termination
- ❌ Stack usage grows; may be inappropriate for embedded targets

```c
void process_recursive(int depth) {
    if (depth >= MAX_DEPTH || done) return;
    process();
    process_recursive(depth + 1);
}
```

**Approvers notified:** @jane-doe @mark-smith
---
```

The agent always generates language-matched code for all three fix options based on the detected repo language.

---

## CODEOWNERS First-Run Setup

Triggered when `.github/CODEOWNERS` does not exist.

1. Agent scans `git log` to identify contributors → presents as suggested developer list
2. Agent asks user to designate approvers from that list (or add external ones)
3. Generates `.github/CODEOWNERS`:

```
# NASA/DOD Code Review — Auto-generated by nasa-dod-code-review skill
# Developers
# @dev1 @dev2 @dev3

# Approvers (required for P0 override)
* @approver1 @approver2

# Language-specific ownership (optional, add as needed)
*.c @approver1
*.py @approver2
```

4. Commits with message: `chore: add CODEOWNERS for NASA/DOD review enforcement`
5. Creates `.github/nasa-dod-review-config.json`:

```json
{
  "solo_dev": false,
  "approvers": ["approver1", "approver2"],
  "last_full_scan": null,
  "target_branch": "main",
  "full_scan_max_age_days": 7
}
```

`last_full_scan` is updated after every full scan and compared against `full_scan_max_age_days` (default: 7) to decide whether to prompt a new full scan before PR review.

---

## Override Logic

| Context | P0 Override Rule |
|---------|-----------------|
| Team project | Requires 2+ peer approvals in GitHub PR |
| Solo developer | Override allowed; recorded in findings with timestamp |

Override log entry format:
```
[OVERRIDE] 2026-05-06T14:32:00Z — P0 "Unbounded loop at flight.c:142"
Overridden by: @harsh (solo developer)
Reason: [developer-provided reason]
```

---

## Standards Sources

Fetched at runtime, cached per session. Full URLs in `standards-sources.md`.

### Universal (always applied)
- NASA Power of Ten Rules (JPL/Jerry Hollingsworth)
- NASA/JPL Institutional Coding Standard for C
- DOD Joint Strike Fighter Air Vehicle C++ Coding Standards (JSF AV C++)
- MISRA C / MISRA C++ (free rule summaries)
- SEI CERT Coding Standards (wiki.sei.cmu.edu — publicly available)

### Language-Specific

| Language | Sources |
|----------|---------|
| C/C++ | JSF AV, NASA JPL C Standard, MISRA, CERT C |
| Python | CERT Python, NASA Python Coding Conventions |
| Go | CERT, official Go code review comments |
| Rust | Rust API Guidelines, CERT (where applicable) |
| Java | CERT Java, DOD Java Coding Standard |
| JavaScript/TS | CERT JS, OWASP JS Security Cheat Sheet |

---

## Tone & Persona

- **Firm but encouraging** — senior engineer who wants you to succeed, not a gatekeeper
- **Assertive on P0/P1** — no hedging. "This must be fixed before merge."
- **Explanatory, not preachy** — explains *why* a rule exists once, doesn't repeat it
- **Acknowledges good work** — opens every report with what the code does well
- **Direct on overrides** — factual, non-judgmental when recording override decisions

### Example Report Opening
```
Good work on the input validation in auth.c — the bounds checking is solid.
Here's what needs attention before this is ready to fly:
```

### Example P0 Assertion
```
🔴 P0/Critical — This blocks merge. Memory allocated in flight_loop() is never
freed under the error path at line 87. In a long-running system this will
exhaust the heap. This is non-negotiable in safety-critical code.
```

---

## Invocation Contexts

| Context | Trigger | Behavior |
|---------|---------|----------|
| Development | `"nasa-dod review"` or `"nasa-dod dev review"` | Full codebase scan |
| PR Review | `"nasa-dod review"` or `"nasa-dod pr review"` | Diff-first; prompt full scan if stale |

---

## Key Design Decisions

- **Agent-agnostic** — plain markdown files; works with any LLM-based coding assistant that can read context files
- **Dual install paths** — global (`~/.agent-skills/`) or per-repo (`.agent-skills/`) depending on user preference
- **README.md as entry point** — standard convention any agent/developer recognizes; no tool-specific loading mechanism required
- **Canonical trigger phrases** — documented in README so users know exactly what to say regardless of which agent they use
- **Modular companion files** — standards, reviewer prompt, severity guide, templates each have one clear purpose and can be updated independently
- **Config file** (`.github/nasa-dod-review-config.json`) is the source of truth for solo/team mode, approvers, and scan history
- **GitHub-first** — CODEOWNERS follows GitHub conventions (`.github/CODEOWNERS`)
- **Three fix options with code** — every finding gives the developer actionable, language-correct choices with trade-off transparency
