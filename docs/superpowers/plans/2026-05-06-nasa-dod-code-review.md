# NASA/DOD Code Review Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, agent-agnostic skill repository that reviews code against NASA/DOD best practices, enforces a P0–P3 severity gate, manages GitHub CODEOWNERS, and outputs findings to terminal and file.

**Architecture:** Six markdown files form the skill — `README.md` orchestrates the full flow; companion files handle standards references, the analysis prompt, severity definitions, CODEOWNERS setup, and report formatting. No code is executed; the agent reads these files as context and follows the instructions within them.

**Tech Stack:** Plain Markdown, GitHub CODEOWNERS convention, JSON config file (`.github/nasa-dod-review-config.json`), git.

---

## File Map

| File | Responsibility |
|------|---------------|
| `README.md` | Skill entry point — full flow, trigger phrases, installation instructions |
| `standards-sources.md` | Authoritative URLs the agent fetches at runtime per language |
| `reviewer-prompt.md` | Focused analysis prompt — instructs the agent how to examine code |
| `severity-guide.md` | P0–P3 definitions with concrete examples, decision criteria |
| `codeowners-template.md` | First-run CODEOWNERS setup walkthrough + template |
| `report-template.md` | Full report structure including finding entry format with 3 fix options |

---

### Task 1: Repository scaffold + README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create the repository root and README.md**

`README.md` is the skill entry point. It must contain: overview, installation instructions (global + per-repo), agent setup one-liner, trigger phrases, the full orchestration flow, and references to companion files.

```markdown
# NASA/DOD Code Review Skill

A standalone, agent-agnostic skill for reviewing code against NASA and DOD
best practices. Works with any LLM-based coding assistant (Claude, Copilot,
Cursor, Gemini, etc.) that can read markdown context files.

---

## Installation

**Global install** (works across all repos):
```bash
git clone https://github.com/<org>/nasa-dod-code-review ~/.agent-skills/nasa-dod-code-review
```

**Per-repo install** (lives alongside the code):
```bash
git clone https://github.com/<org>/nasa-dod-code-review .agent-skills/nasa-dod-code-review
# Optionally add to .gitignore or commit it — your choice
```

Add one line to your agent context file (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`,
`copilot-instructions.md`, etc.):
```
When you see "nasa-dod review", load and follow .agent-skills/nasa-dod-code-review/README.md
```

---

## Trigger Phrases

| Phrase | Behavior |
|--------|----------|
| `nasa-dod review` | Auto-detects context (dev or PR) and runs accordingly |
| `nasa-dod dev review` | Forces full codebase scan |
| `nasa-dod pr review` | Forces PR/diff mode |

---

## How You Work (Agent Instructions)

You are a senior engineer conducting a safety-critical code review using NASA
and DOD coding standards. Your tone is firm and encouraging — you want the
developer to succeed, not to block them arbitrarily. Be assertive on P0/P1
issues with no hedging. Explain why a rule exists once; don't repeat it.
Open every report by acknowledging what the code does well.

### Step 1 — CODEOWNERS Check
Check whether `.github/CODEOWNERS` exists in the repo.
- If it does NOT exist: load and follow `codeowners-template.md` before proceeding.
- If it exists: continue to Step 2.

### Step 2 — Detect Context
Determine:
- **Language(s):** Scan file extensions and build files to identify all languages present.
- **Solo or team:** Read `.github/nasa-dod-review-config.json`. If `solo_dev` is true, one developer; otherwise team rules apply. If config doesn't exist yet (created in Step 1), use the value just set.
- **Mode:** If the trigger was `nasa-dod pr review` or you can detect a PR context (diff available, branch comparison), use PR mode. Otherwise use dev mode.

### Step 3 — Fetch Standards
Load `standards-sources.md`. Fetch the sources listed for:
1. Universal standards (always)
2. Each language detected in Step 2

Cache fetched content for the duration of this session — do not re-fetch.

### Step 4 — Determine Scan Scope
**PR mode:**
- Read `last_full_scan` from `.github/nasa-dod-review-config.json`.
- If null or older than `full_scan_max_age_days` (default 7): tell the user:
  > "No recent full scan found on this branch. I strongly recommend running
  > `nasa-dod dev review` first to establish a baseline. Want to proceed with
  > diff-only anyway?"
- If recent: analyze only the changed files/diff.

**Dev mode:**
- Analyze the full codebase.
- After completing the report, update `last_full_scan` to the current ISO timestamp in `.github/nasa-dod-review-config.json`.

### Step 5 — Analyze Code
Load `reviewer-prompt.md` and follow its instructions to perform the analysis pass.
Apply universal standards first, then language-specific standards for each detected language.

### Step 6 — Generate Findings
Load `severity-guide.md` to classify each issue found.
Load `report-template.md` to format the output.

For every finding:
- Assign a severity level (P0–P3)
- Cite the specific rule violated
- Write the "why this must be fixed" explanation
- Generate three fix options with pros/cons and language-correct code examples
- Tag approvers (@username) on P0 and P1 findings

### Step 7 — Apply Gate Logic
**If P0 findings exist:**
- State clearly: "🔴 This PR is BLOCKED. The following P0/Critical issues must be
  resolved before merge:"
- List each P0 with full reasoning.
- Check `solo_dev` in config:
  - `true`: Offer override with prompt: "As a solo developer you may override this
    block. Please provide your reason, and it will be recorded in the findings."
    Record the override in the report's Override Log with timestamp and reason.
  - `false`: State: "Override requires 2 or more peer approvals on this PR.
    Approvers have been tagged above."

**If no P0 findings:** state the gate status as PASSED.

### Step 8 — Output
1. Print the full report to terminal/chat following the structure in `report-template.md`.
2. Write the report to `reports/code-review-YYYY-MM-DD.md` in the repo being reviewed
   (create the `reports/` directory if it doesn't exist).
3. If this was a full scan (dev mode), update `.github/nasa-dod-review-config.json`:
   set `last_full_scan` to the current UTC ISO 8601 timestamp.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "feat: add README.md skill entry point and orchestration flow"
```

---

### Task 2: standards-sources.md

**Files:**
- Create: `standards-sources.md`

- [ ] **Step 1: Write the standards sources file**

This file is fetched by the agent at runtime. It must list authoritative, publicly accessible URLs grouped by universal and language-specific. Include a brief description of what each source covers so the agent knows what to extract from it.

```markdown
# Standards Sources

This file lists the authoritative sources the agent fetches and digests before
performing a code review. Fetch all Universal sources on every run. Fetch
language-specific sources only for languages detected in the target repo.

Cache all fetched content for the duration of the session.

---

## Universal (fetch on every run)

### NASA Power of Ten Rules
- **URL:** https://spinroot.com/gerard/pdf/P10.pdf
- **What to extract:** All 10 rules with their rationale. Apply to every language.

### SEI CERT Coding Standards (portal)
- **URL:** https://wiki.sei.cmu.edu/confluence/display/seccode/SEI+CERT+Coding+Standards
- **What to extract:** Landing page links to per-language standards. Use as index.

### DOD Joint Strike Fighter AV C++ Coding Standards
- **URL:** https://www.stroustrup.com/JSF-AV-rules.pdf
- **What to extract:** All numbered rules. Especially applicable to C/C++ but
  principles around error handling, resource management, and complexity apply universally.

### NASA/JPL Institutional Coding Standard for C
- **URL:** https://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf
- **What to extract:** All rules. Universally applicable principles include:
  no dynamic memory after init, no recursion without depth bounds, no function
  pointers, single point of return preferred.

---

## Language-Specific

### C / C++
- **CERT C:** https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard
- **CERT C++:** https://wiki.sei.cmu.edu/confluence/display/cplusplus/SEI+CERT+C%2B%2B+Coding+Standard
- **MISRA C (public summary):** https://www.misra.org.uk/misra-c/
- Additional: JSF AV and NASA JPL C (already in Universal above)

### Python
- **CERT Python:** https://wiki.sei.cmu.edu/confluence/display/python/SEI+CERT+Python+Coding+Standard
- **NASA Python Coding Conventions:** https://github.com/nasa/NASA-SW-VnV-Std-18011-Python

### Go
- **CERT Go:** https://wiki.sei.cmu.edu/confluence/display/golang/SEI+CERT+Go+Coding+Standard
- **Go Code Review Comments (official):** https://github.com/golang/go/wiki/CodeReviewComments

### Rust
- **Rust API Guidelines:** https://rust-lang.github.io/api-guidelines/
- **CERT Rust (where applicable):** https://wiki.sei.cmu.edu/confluence/display/rust

### Java
- **CERT Java:** https://wiki.sei.cmu.edu/confluence/display/java/SEI+CERT+Oracle+Coding+Standard+for+Java
- **DOD Java Coding Standard:** https://web.archive.org/web/20111018064908/http://java.sun.com/docs/codeconv/

### JavaScript / TypeScript
- **CERT JS:** https://wiki.sei.cmu.edu/confluence/display/js/SEI+CERT+JavaScript+Coding+Standard
- **OWASP JS Security Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/JavaScript_Security_Cheat_Sheet.html
```

- [ ] **Step 2: Commit**

```bash
git add standards-sources.md
git commit -m "feat: add standards-sources.md with NASA/DOD/language-specific URLs"
```

---

### Task 3: severity-guide.md

**Files:**
- Create: `severity-guide.md`

- [ ] **Step 1: Write the severity guide**

This file is the agent's classification reference. Every finding must be mapped to a level. Include concrete decision criteria and examples per level so the agent classifies consistently, not subjectively.

```markdown
# Severity Guide

Use this guide to classify every finding. When in doubt between two levels,
choose the higher severity. Safety-critical context should bias toward higher severity.

---

## P0 / Critical — BLOCKS MERGE

**Definition:** A defect that poses a direct risk to system safety, security,
reliability, or data integrity. In a deployed system, this could cause crashes,
data loss, exploits, deadlocks, or undefined behavior.

**Decision criteria (any one of these → P0):**
- Undefined behavior (buffer overflow, integer overflow, use-after-free, null deref)
- Unbounded loop or recursion with no guaranteed termination
- Dynamic memory allocation after initialization in safety-critical context
- Missing error handling on a code path that can fail
- Hardcoded secrets, credentials, or cryptographic material
- Resource acquired but never released (file, socket, memory, lock)
- Race condition on shared mutable state
- Input used without validation or sanitization before use in sensitive context

**Examples:**
- `malloc()` called in a flight-critical loop with no paired `free()`
- `strcpy()` with user-supplied input and no bounds check
- A mutex locked inside an interrupt handler with no timeout

---

## P1 / Major — Must be resolved before next release

**Definition:** A significant violation of coding standards that increases risk,
reduces auditability, or makes the code difficult to reason about safely. Not
immediately catastrophic but creates conditions for future P0s.

**Decision criteria (any one of these → P1):**
- Function exceeds 60 lines or has cyclomatic complexity > 10
- Global mutable state accessed from multiple modules without synchronization
- Magic numbers used in safety-relevant calculations
- Error return value explicitly ignored (e.g., `(void)result`)
- Missing or inadequate test coverage on a critical path
- Goto used in a way that creates non-obvious control flow
- Non-deterministic behavior in a deterministic context

**Examples:**
- A 200-line function with 15 branches and no unit tests
- `errno` not checked after a syscall that can fail
- `#define TIMEOUT 3000` used in 12 places with no named constant

---

## P2 / Minor — Should be fixed in this sprint

**Definition:** A code quality or maintainability issue that doesn't pose
immediate risk but violates standards and will complicate future work.

**Decision criteria:**
- Naming doesn't follow language/project conventions
- Comment describes *what* the code does, not *why*
- Dead code (unreachable, unused variables/imports)
- Function does more than one thing (SRP violation)
- Inconsistent error handling strategy within a module
- Missing or stale documentation for a public API

**Examples:**
- `int x` used as a loop variable in a non-trivial algorithm
- A public function with no docstring in a Python module
- `if (flag == true)` instead of `if (flag)`

---

## P3 / Advisory — No action required

**Definition:** A best-practice observation. Flagged for awareness; developer
may choose to address or consciously defer.

**Decision criteria:**
- Alternative approach would be marginally cleaner but current code is correct
- Style preference not enforced by project standards
- Performance micro-optimization opportunity
- Suggestion to add defensive assertion that isn't strictly necessary

**Examples:**
- `const` could be added to a parameter that isn't modified
- A loop could be expressed more clearly as a standard library call
- An inline comment could be more descriptive
```

- [ ] **Step 2: Commit**

```bash
git add severity-guide.md
git commit -m "feat: add severity-guide.md with P0-P3 definitions and examples"
```

---

### Task 4: reviewer-prompt.md

**Files:**
- Create: `reviewer-prompt.md`

- [ ] **Step 1: Write the reviewer prompt**

This is the focused analysis pass prompt. It must tell the agent exactly how to read the code, what to look for in what order, and how to structure raw findings before they go through the report template. It must be language-aware and reference the severity guide.

```markdown
# Reviewer Prompt

This file contains your analysis instructions. Follow them in order for every
code review pass. You have already fetched the standards (from `standards-sources.md`)
and know the target language(s). Now you examine the code.

---

## Analysis Order

Work through the code in this order. Findings accumulate — don't stop at the first issue.

### Pass 1 — Safety & Security (P0 candidates)
Scan for anything that could cause undefined behavior, crashes, data corruption,
or security exploits. For each language, apply the relevant CERT rules and NASA/DOD
rules simultaneously. Ask yourself:
- Is every pointer/reference guaranteed valid before use?
- Is every buffer access bounds-checked?
- Is every resource that is acquired also released on every exit path?
- Is every input validated before use?
- Are there any unbounded loops or recursion without depth limits?
- Is any sensitive data (keys, tokens, passwords) hardcoded or logged?
- Are there race conditions on shared state?

### Pass 2 — Error Handling & Control Flow (P0/P1 candidates)
- Is every function call that can fail checked for errors?
- Are error codes propagated or swallowed?
- Does every error path release acquired resources?
- Is control flow comprehensible? (No spaghetti gotos, no deeply nested conditionals)

### Pass 3 — Complexity & Structure (P1/P2 candidates)
- Do any functions exceed 60 lines or cyclomatic complexity of 10?
- Are there global variables accessible from multiple modules?
- Are magic numbers used in calculations?
- Does each function do exactly one thing?

### Pass 4 — Standards Compliance (P1/P2 candidates)
Apply the specific rules from the fetched standards for each detected language.
Flag violations by rule number/name wherever possible.

### Pass 5 — Code Quality & Maintainability (P2/P3 candidates)
- Naming conventions
- Dead code
- Comment quality (explains why, not what)
- Public API documentation
- Consistency within the module

---

## What "Good Work" Looks Like

Before generating findings, note two to five things the code does well.
This becomes the "What looks good" section of the report. Be specific —
"good error handling" is vague; "consistent use of early-return guards to
keep the happy path readable" is useful.

---

## Raw Finding Format

For each issue found, record it internally in this format before running it
through the report template:

```
SEVERITY: [P0/P1/P2/P3]
FILE: path/to/file.ext:line_number
RULE: [Standard name] — [Rule number or name]
LANGUAGE: [detected language]
ISSUE: [one sentence description]
WHY: [why this matters — safety, reliability, auditability]
```

Once all passes are complete, hand off to `report-template.md` to format findings
into the final report. Generate three fix options with language-correct code for
each finding at that stage.

---

## Language-Specific Checklist Additions

### C / C++
- No `malloc`/`calloc`/`realloc` after program initialization in safety-critical paths
- No `gets()`, `scanf("%s")` without bounds — use `fgets()` or `scanf("%Ns")`
- Every `switch` has a `default` case
- No implicit fallthrough in `switch` without explicit comment
- `const` applied to all pointers and parameters that are not modified
- No recursion without an explicit depth-limit guard

### Python
- No `eval()` or `exec()` on untrusted input
- All exceptions caught specifically — no bare `except:`
- No mutable default arguments in function signatures
- All public functions have docstrings
- No use of `pickle` on untrusted data

### Go
- Every `error` return value checked — never `_` a returned error
- No goroutine launched without a clear shutdown/cancellation path
- `defer` not used in hot loops
- No use of `unsafe` package without documented justification

### Rust
- No `unwrap()` or `expect()` in production paths — use `?` or explicit match
- No `unsafe` blocks without a `// SAFETY:` comment explaining the invariant
- No use of `std::mem::forget` on types with destructors without justification

### Java
- No raw types — always parameterize generics
- No `catch (Exception e)` without re-throw or specific handling
- All resources opened in `try` blocks use try-with-resources
- No `System.exit()` in library code

### JavaScript / TypeScript
- No `eval()` or `new Function()` on untrusted input
- `===` used everywhere — never `==`
- All Promises have `.catch()` handlers or are awaited in try/catch
- No `any` type in TypeScript without documented justification
- No `innerHTML` assignment with untrusted content — use `textContent`
```

- [ ] **Step 2: Commit**

```bash
git add reviewer-prompt.md
git commit -m "feat: add reviewer-prompt.md with multi-pass analysis instructions"
```

---

### Task 5: codeowners-template.md

**Files:**
- Create: `codeowners-template.md`

- [ ] **Step 1: Write the CODEOWNERS setup guide**

This file is loaded only on first run when `.github/CODEOWNERS` is absent. It walks the agent through collecting team information, generating the file, and creating the config.

```markdown
# CODEOWNERS First-Run Setup

This is your first time running the NASA/DOD code review skill in this repository.
Before any code analysis can begin, you need to establish ownership and configuration.
Follow these steps exactly.

---

## Step 1 — Identify Contributors

Run the following to extract existing contributors from git history:
```bash
git log --format="%ae %an" | sort -u
```

Present the results to the user:
> "I found the following contributors in this repo's git history. I'll use this
> to suggest your team list:"
> [list names and emails]

---

## Step 2 — Collect Developers and Approvers

Ask the user:
> "Please confirm or update the developer list, and tell me which of these
> (or any additional GitHub usernames) should be designated as **approvers**.
> Approvers are required to sign off on any P0/Critical override in team projects.
> You need at least one approver."

Wait for the response. Record:
- `developers`: list of GitHub usernames
- `approvers`: list of GitHub usernames (subset or superset of developers)

---

## Step 3 — Determine Solo or Team

Ask the user:
> "Is this a solo project (just you) or a team project?
> - Solo: you can override P0 blocks yourself, but overrides are recorded.
> - Team: P0 overrides require 2+ approver sign-offs."

Record `solo_dev: true` or `solo_dev: false`.

---

## Step 4 — Determine Target Branch

Ask the user:
> "What is your primary integration branch? (e.g., `main`, `master`, `develop`)"

Record as `target_branch`.

---

## Step 5 — Generate .github/CODEOWNERS

Create the directory if needed: `mkdir -p .github`

Write `.github/CODEOWNERS`:
```
# NASA/DOD Code Review — Auto-generated by nasa-dod-code-review skill
# Edit this file to update ownership assignments.

# Developers (informational — not enforced by GitHub)
# @dev1 @dev2 @dev3

# Approvers — required for P0/Critical override approval
* @approver1 @approver2

# Language-specific ownership (uncomment and customize as needed)
# *.c      @approver1
# *.py     @approver2
# *.go     @approver1 @approver2
```

Replace placeholder usernames with the actual values collected above.

---

## Step 6 — Generate .github/nasa-dod-review-config.json

Write `.github/nasa-dod-review-config.json`:
```json
{
  "solo_dev": false,
  "developers": ["dev1", "dev2"],
  "approvers": ["approver1", "approver2"],
  "last_full_scan": null,
  "target_branch": "main",
  "full_scan_max_age_days": 7
}
```

Replace values with what was collected. Set `solo_dev` to `true` if applicable.

---

## Step 7 — Commit

```bash
git add .github/CODEOWNERS .github/nasa-dod-review-config.json
git commit -m "chore: add CODEOWNERS and nasa-dod review config"
```

---

## Done

First-run setup complete. Return to `README.md` Step 2 and continue the review.
```

- [ ] **Step 2: Commit**

```bash
git add codeowners-template.md
git commit -m "feat: add codeowners-template.md for first-run team setup"
```

---

### Task 6: report-template.md

**Files:**
- Create: `report-template.md`

- [ ] **Step 1: Write the report template**

This is the formatting layer. Every finding produced in the analysis pass is rendered using this template. The agent reads this file when generating the final output. Include the exact structure, all section headers, the finding entry format with three fix options and code, the override log, and the summary header.

```markdown
# Report Template

Use this template to format the final code review report. Generate it twice:
once as terminal/chat output and once written to `reports/code-review-YYYY-MM-DD.md`
(replace with actual date). Create the `reports/` directory if it does not exist.

---

## Full Report Structure

```markdown
# NASA/DOD Code Review Report
**Date:** YYYY-MM-DD
**Branch:** [branch name]
**Scan type:** [Full scan / Diff scan (PR: base...head)]
**Languages detected:** [e.g., C, Python]
**Skill version:** nasa-dod-code-review @ [git tag or commit]

## Summary
| Severity | Count |
|----------|-------|
| 🔴 P0 / Critical | N |
| 🟠 P1 / Major    | N |
| 🟡 P2 / Minor    | N |
| 🔵 P3 / Advisory | N |
| **Total**        | N |

**Gate status:** 🔴 BLOCKED — N critical issue(s) must be resolved before merge.
<!-- OR -->
**Gate status:** ✅ PASSED — No critical issues found.

---

## What Looks Good

[2–5 specific, concrete observations about what the code does well.
Be precise. "Good use of early-return guards in auth.c to keep the happy
path flat and readable." not "code looks clean."]

---

## 🔴 P0 / Critical

<!-- Repeat the finding block below for each P0 finding -->

### [P0/Critical] [Short issue title]
**File:** `path/to/file.ext:line_number`
**Rule:** [Standard name] — [Rule number or name]
**Language:** [Language]

**Why this must be fixed:** [One to three sentences. What goes wrong in a real
system if this isn't fixed. Be specific about the failure mode.]

#### Fix Options

**Option 1 — [Short name]** *(recommended)*
[One sentence describing the approach.]
- ✅ [Pro]
- ✅ [Pro if applicable]
- ❌ [Con]

```[language]
// actual code example in the repo's language
```

**Option 2 — [Short name]**
[One sentence describing the approach.]
- ✅ [Pro]
- ❌ [Con]
- ❌ [Con if applicable]

```[language]
// actual code example
```

**Option 3 — [Short name]**
[One sentence describing the approach.]
- ✅ [Pro]
- ❌ [Con]

```[language]
// actual code example
```

**Approvers notified:** @approver1 @approver2

---

## 🟠 P1 / Major

<!-- Same finding block format as P0 — repeat for each P1 finding -->
<!-- Approvers notified line is included on P1 findings as well -->

---

## 🟡 P2 / Minor

<!-- Same finding block format — three fix options with code -->
<!-- No "Approvers notified" line on P2 -->

---

## 🔵 P3 / Advisory

<!-- Same finding block format — three fix options with code -->
<!-- No "Approvers notified" line on P3 -->

---

## Override Log

<!-- Only include this section if any overrides occurred this session -->
<!-- If no overrides, omit the section entirely -->

| Timestamp | Severity | Issue | Overridden by | Reason |
|-----------|----------|-------|---------------|--------|
| 2026-05-06T14:32:00Z | P0/Critical | Unbounded loop at flight.c:142 | @harsh (solo developer) | Deadline pressure; will fix in next sprint |

---
*Report generated by [nasa-dod-code-review](https://github.com/<org>/nasa-dod-code-review)*
```

---

## Tone Reminders

- Open with "What Looks Good" before any findings — always.
- On P0/P1: state the problem directly. "This must be fixed before merge."
  No softening phrases like "you might want to" or "consider possibly".
- On P2/P3: use encouraging language. "This is easy to clean up —
  here are three ways to approach it."
- On overrides: record factually, no judgment. "Override recorded. Developer
  acknowledged risk."
- Never repeat the same rule explanation twice in a single report.
```

- [ ] **Step 2: Commit**

```bash
git add report-template.md
git commit -m "feat: add report-template.md with full findings format and fix options"
```

---

### Task 7: Repository finalization

**Files:**
- Create: `.gitignore`
- Create: `LICENSE` (MIT)
- Create: `CHANGELOG.md`

- [ ] **Step 1: Add .gitignore**

```
# Reports generated in target repos — not part of the skill itself
reports/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Add LICENSE (MIT)**

```
MIT License

Copyright (c) 2026 [Author]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Add CHANGELOG.md**

```markdown
# Changelog

## [0.1.0] — 2026-05-06

### Added
- Initial release
- README.md orchestration flow with full agent instructions
- P0–P3 severity scale with decision criteria and examples
- Multi-pass reviewer prompt (safety, error handling, complexity, standards, quality)
- Language-specific checklists: C/C++, Python, Go, Rust, Java, JavaScript/TypeScript
- GitHub CODEOWNERS first-run setup with config file
- Report template with three fix options per finding (pros/cons + language code)
- Standards sources: NASA Power of Ten, JSF AV C++, NASA JPL C, SEI CERT, MISRA, OWASP
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore LICENSE CHANGELOG.md
git commit -m "chore: add .gitignore, LICENSE, and CHANGELOG for initial release"
```

---

### Task 8: Tag initial release

- [ ] **Step 1: Create v0.1.0 tag**

```bash
git tag -a v0.1.0 -m "Initial release — NASA/DOD code review skill"
```

- [ ] **Step 2: Verify all files are present**

```bash
ls -1
```

Expected output:
```
CHANGELOG.md
LICENSE
README.md
codeowners-template.md
report-template.md
reviewer-prompt.md
severity-guide.md
standards-sources.md
```

---

## Self-Review Against Spec

| Spec Requirement | Covered by Task |
|-----------------|-----------------|
| Universal NASA/DOD principles | Task 2 (standards-sources.md), Task 4 (reviewer-prompt.md) |
| Language-specific rules auto-detected | Task 1 (README Step 2), Task 4 (language checklists) |
| PR mode: diff-first, prompt full scan if stale | Task 1 (README Steps 3–4) |
| P0–P3 severity scale | Task 3 (severity-guide.md) |
| P0 blocks merge with assertion | Task 1 (README Step 7), Task 6 (report-template.md) |
| 2+ peer approvals for P0 override on teams | Task 1 (README Step 7) |
| Solo dev override with notation | Task 1 (README Step 7), Task 6 (report-template.md override log) |
| CODEOWNERS first-run setup | Task 5 (codeowners-template.md) |
| Developer + approver lists | Task 5 |
| Config file with last_full_scan, solo_dev | Task 5 |
| Tag approvers on P0/P1 | Task 1 (README Step 6), Task 6 (finding format) |
| Findings to terminal + file | Task 1 (README Step 8), Task 6 |
| Three fix options with code per finding | Task 4 (reviewer-prompt.md), Task 6 (report-template.md) |
| Pros/cons per fix option | Task 6 (report-template.md) |
| Firm but friendly tone | Task 1 (README persona), Task 4, Task 6 |
| Agent-agnostic, no tool-specific loading | Task 1 (plain markdown, trigger phrases) |
| Dual install paths (global + per-repo) | Task 1 (README installation section) |
| Canonical trigger phrases | Task 1 (README trigger table) |
| Standards fetched from authoritative sources | Task 2 (standards-sources.md with URLs) |
| 7-day full scan staleness default | Task 5 (config `full_scan_max_age_days`) |
