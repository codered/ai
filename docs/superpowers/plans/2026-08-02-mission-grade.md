# mission-grade Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `skills/mission-grade/` — a superset skill that applies NASA/DoD engineering standards to code and ASD-STE100 mechanical writing rules to the prose that ships with it, from a single auto-activating trigger, for writing, refactoring, and reviewing code.

**Architecture:** Self-contained hot path with delegated depth. `SKILL.md` handles a normal write, refactor, or review with no additional file loaded — it carries the surface map, the precedence rules, the condensed standards, the six gates, and the self-check. Three companion files under `references/` hold the material neither parent skill contains. Sibling skills (`nfc`, `applying-nasa-dod-coding-standards`, `nasa-dod-code-review`) are named as optional depth and are never required, so the directory works when lifted out of the repository alone.

**Tech Stack:** Plain Markdown with YAML frontmatter (`name` + `description`), git. No executable code ships. Verification is done by dispatching fresh subagents against the built files and checking observable behavior.

**Spec:** `docs/superpowers/specs/2026-08-02-mission-grade-skill-design.md` (commit `17e3811`)

---

## Global Constraints

Every task's requirements implicitly include this section.

- **No skill may depend on another.** README.md:440 states the repo philosophy: "One skill, one job. Each skill does exactly one thing well. No skill depends on another, and none require a specific agent or platform." `skills/mission-grade/` must function with the other skill directories absent. Every pointer to a sibling skill must be phrased as optional depth, and must state what to do when the file is not present.
- **Skill entry point format.** `SKILL.md` starts with a YAML frontmatter block containing exactly `name` and `description`, matching `skills/nfc/SKILL.md` and `skills/nasa-dod-code-review/SKILL.md`.
- **Skill name:** `mission-grade`. Directory: `skills/mission-grade/`.
- **SKILL.md length target:** approximately 300 lines, and under 400 in any case. Siblings for scale: `applying-nasa-dod-coding-standards/SKILL.md` is 442 lines, `nfc/SKILL.md` is 265. The ceiling was raised from 380 to 400 during execution: the mandatory attribution block and the optional-depth table put the finished file at 390, and neither is cuttable.
- **Line wrapping:** wrap prose at 95 characters, matching `skills/nfc/SKILL.md`. Do not wrap table rows.
- **Dogfooding boundary — read this carefully.** The instruction prose inside `SKILL.md` and the `references/` files is *conversation side* under the skill's own dividing line, so it is NOT bound by STE modes. Write it clearly and without hedging, but do not flatten it to 20-word sentences. The *code samples and their comments, docstrings, and error strings* inside `references/examples.md` ARE artifact side and MUST obey the surface map exactly — they are the worked demonstration.
- **Emoji:** do not use emoji in the skill's own instruction prose. The only emoji permitted anywhere in the skill are inside worked examples that demonstrate the required NASA/DoD review callouts.
- **Attribution is mandatory.** `SKILL.md` must end with the attribution block specified in Task 7. Do not vendor, quote, or reproduce the ASD-STE100 approved-word dictionary anywhere.
- **Never claim conformance.** No file may state or imply that the skill certifies ASD-STE100 conformance.
- **Commits:** conventional-commit style matching repo history (`feat(mission-grade): ...`, `docs(mission-grade): ...`). End every commit message with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  ```

### Verification method (used by every task)

Prose skills have no unit tests. Every verification step in this plan uses the same harness, and it must be run exactly this way:

1. Dispatch a **fresh** subagent with the Agent tool (`subagent_type: general-purpose`, `run_in_background: false`).
2. The subagent's prompt contains **only**: the absolute path(s) to the skill file(s) built so far, an instruction to read them and follow them, and the scenario input.
3. **Never tell the subagent what behavior is expected**, which scenario is being run, or that it is being tested. A subagent told the pass condition will produce it regardless of the file's quality, which makes the test worthless.
4. Compare the returned output against the stated pass condition.
5. If it fails, fix the skill file and re-run the same scenario. Do not adjust the pass condition to match the output.

---

## File Map

| File | Responsibility |
|------|---------------|
| `skills/mission-grade/SKILL.md` | Entry point — frontmatter, dividing line, surface map, precedence rules, condensed standards, six gates, self-check, optional-depth pointers, attribution |
| `skills/mission-grade/references/ste-for-code.md` | STE word rules applied to identifiers, user-facing strings, and comments, with before/after pairs and code-prose substitutions |
| `skills/mission-grade/references/prose-gate.md` | Gate 6 detail — what to inspect, severity mapping, finding template, and an explicit not-a-finding list |
| `skills/mission-grade/references/examples.md` | Three end-to-end worked examples: write, refactor, review |
| `README.md` (repo root) | New skill card; skill-count badge bumped from 10 to 11 |

`SKILL.md` is built across Tasks 1–3 in three passes (policy, standards, review) because each pass is independently verifiable and a reviewer could reject one while approving another. The reference files follow, then registration.

---

### Task 1: `SKILL.md` — frontmatter, dividing line, surface map, precedence

**Files:**
- Create: `skills/mission-grade/SKILL.md`

**Interfaces:**
- Produces: the file `skills/mission-grade/SKILL.md`, ending after the "Precedence" section. Tasks 2 and 3 append to it. The surface-map table and the three precedence rules defined here are referenced by name in Tasks 3, 4, and 5.

- [ ] **Step 1: Create the directory**

```bash
mkdir -p /home/code/development/ai/skills/mission-grade/references
```

- [ ] **Step 2: Write the file**

Write this content verbatim to `skills/mission-grade/SKILL.md`:

````markdown
---
name: mission-grade
description: >
  Use this skill when writing, refactoring, or reviewing production code. It applies NASA/DoD
  engineering standards to the code and ASD-STE100 Simplified Technical English rules to the
  prose that ships with it — comments, docstrings, error messages, identifiers, and commit
  messages. Triggers include: "write", "implement", "refactor", "clean up", "review this code",
  "code review", "mission grade", "nasa-dod", "safety-critical", "production-ready", or any
  request to add a feature, fix a bug, or improve existing code. Also use it when establishing
  coding standards for a project, auditing code for reliability or security, or preparing a
  pull request.
---

# mission-grade

Applies two standards at once, from one trigger:

- **NASA/DoD engineering standards** to the code — the Power of Ten, the DoD secure-coding
  baseline, and test-driven development.
- **ASD-STE100 mechanical writing rules** to the prose that ships with the code — comments,
  docstrings, error messages, identifiers, and commit messages.

This skill is self-contained. It needs no other skill to function.

---

## The dividing line

**STE governs the artifact. NASA/DoD governs the conversation about the artifact.**

If it is committed to the repository, STE binds it. If it is you talking to the user — a
finding, a rule citation, a gate result, a chat reply — NASA/DoD's communication rules bind it
and STE does not apply.

That one line resolves every conflict between the two standards. Apply it before reaching for
any other rule.

---

## Surface map

| Surface | Governed by | STE mode |
|---|---|---|
| Procedural comments (how-to, setup steps) | STE | `strict` |
| Rationale comments (why a decision was made) | STE | `clear` |
| Docstrings, module headers | STE | `clear` |
| Identifiers | STE word rules only | word rules only — see `references/ste-for-code.md` |
| Error, log, and CLI-help strings | STE | `strict` |
| Commit messages, PR descriptions | STE | `clear` |
| Review findings, rule citations, callouts, gate status, option lists | NASA/DoD | exempt |
| Chat replies about the work | NASA/DoD | exempt |

The table is fixed. Do not offer to change it, and do not adjust it on request. If the `nfc`
skill is available in this environment, point the user there for freely selectable modes; if it
is not, say so in one line and leave the table as it stands.

**Procedural or rationale?** A comment is procedural if it tells the reader to do something:
setup steps, an ordering the caller must obey, a manual recovery procedure. It is rationale if
it explains why the code is as it is. When a comment does both, split it — the procedural part
becomes a numbered list in `strict`, the rationale stays in prose in `clear`. When the split is
not worth it, apply `clear` and put any instruction on its own line.

### The two modes, in full

`clear` — every sentence 25 words or fewer. Paragraphs 6 sentences or fewer, one topic each.
Active voice; passive only where the actor is genuinely unknown. Simple present, past, or
future. Articles required. State the conclusion first, then the reasoning. Define a technical
term on first use. Use a list for any 3 or more items.

`strict` — everything in `clear`, and: procedural sentences 20 words or fewer. Exactly one
instruction per sentence. Imperative verb first in every step. No present perfect — use the
simple past. No `-ing` form except as a technical noun. Noun clusters 3 words or fewer. Never
drop an article. No idioms, metaphors, or figures of speech. No emoji. Hedge only when the
uncertainty is real, and state its cause. Put a warning before the step it applies to.

---

## Precedence

Apply in this order. A higher rule beats a lower one.

**1. Accuracy wins over everything.** If an STE constraint would make a comment, docstring, or
error message wrong, misleading, or falsely certain, keep it accurate and state in one line
which constraint you relaxed and why. This applies to accuracy only. It is never an escape
hatch for convenience, brevity, or effort.

**2. NASA/DoD wins over STE.** Wherever the two give conflicting instructions on the same
output, follow NASA/DoD.

**3. STE binds everything else** the surface map assigns to it.

### The three resolved conflicts

**Emoji.** NASA/DoD requires a warning callout for immediate-action items and a status marker
for a blocked gate. STE prohibits emoji. Both hold: emoji are **required** in review output and
callouts, and **prohibited** in comments, docstrings, and user-facing strings.

**Explanation versus sentence caps.** "Cite the rule, state the failure mode, give 2-3 options
with tradeoffs" is explanatory prose, and `strict` caps sentences at 20 words. Findings and
tradeoff prose are conversation side, so the caps never touch them. State a genuinely
conditional tradeoff as conditional.

**Identifier naming versus codebase consistency.** STE caps noun clusters at 3 words and
requires one term per concept. NASA/DoD requires naming consistent with the surrounding
codebase. **Consistency wins.** STE word rules apply only to concepts the current change
introduces. Do not rename existing symbols to satisfy cluster length. Do not offer such renames
unless the user asks — a sweeping rename is its own pull request.

**Quoted material is never rewritten.** STE applies to prose you author, never to code, output,
or text you cite.
````

- [ ] **Step 3: Verify — activation (Scenario 1)**

Dispatch a subagent per the global verification method with this exact prompt:

```
Read every SKILL.md under /home/code/development/ai/skills/ and read only their YAML
frontmatter (the `name` and `description` fields). A user has just said:

    "refactor this module"

List which skill or skills apply, and quote the sentence from the frontmatter that made
you pick each one. Do not read the body of any skill file.
```

**Pass:** `mission-grade` appears in the returned list.
**Fail:** it does not. Widen the trigger verbs in the `description` field and re-run.

- [ ] **Step 4: Verify — surface classification**

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it.

For each item below, state whether ASD-STE100 rules apply to it, and if so at which mode:

1. A docstring on a public function
2. The text of a code-review finding you are writing for the user
3. An error message shown to an end user
4. A comment listing the four steps to regenerate a certificate
5. A comment explaining why a mutex is acquired in a specific order
6. A commit message body
7. A warning callout telling the user to rotate a leaked key right now
8. The name of a new class you are introducing

Answer as a list. Give no other commentary.
```

**Pass:** items 1, 3, 4, 5, 6, 8 are STE-bound and items 2 and 7 are exempt, with modes
matching the surface map (1=`clear`, 3=`strict`, 4=`strict`, 5=`clear`, 6=`clear`, 8=word
rules only).
**Fail:** any misclassification, especially 2 or 7 being treated as STE-bound. That means the
dividing line is not stated sharply enough — tighten it and re-run.

- [ ] **Step 5: Verify — accuracy escape hatch (Scenario 6)**

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it.

Write the docstring for this function. Output only the docstring.

def flush_write_buffer(self) -> bool:
    # Returns True when the buffer reached durable storage. On network filesystems
    # the underlying fsync may report success before the data is durable, so a True
    # return is not a durability guarantee there. On local filesystems it is.
```

**Pass:** the docstring preserves the conditional durability caveat — it does not flatten the
behavior into an unconditional "returns True when the data is durable." If the agent noted a
relaxed constraint in one line, that is also a pass.
**Fail:** the caveat is dropped or stated as unconditional. Strengthen precedence rule 1 with an
explicit "do not drop a qualifier to meet a word cap" sentence and re-run.

- [ ] **Step 6: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/SKILL.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add skill policy core — dividing line, surface map, precedence

STE governs the artifact, NASA/DoD governs the conversation about it.
Resolves the emoji, sentence-cap, and identifier-naming conflicts.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `SKILL.md` — condensed standards and the write/refactor flows

**Files:**
- Modify: `skills/mission-grade/SKILL.md` (append after the Precedence section)

**Interfaces:**
- Consumes: the surface map and precedence rules from Task 1.
- Produces: the Power of Ten one-liners, the DoD baseline one-liners, the Iron Law, and the
  Write and Refactor flows. Task 3's gates cite these rules by number.

- [ ] **Step 1: Append the standards and flows**

Append this content verbatim to `skills/mission-grade/SKILL.md`:

````markdown
---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write a failing test, watch it fail for the right reason, write the minimum code to pass, then
refactor with tests green. Every cycle. No exception for "simple", "urgent", or "obvious".

Show the failing output in your reply. The red test is the receipt that proves the bug was
reproduced, and the same output turning green is the proof the fix worked.

When the user offers a reason to skip it — "too simple to test", "I already tested it
manually", "I'll add the test after", "it's just a prototype", "no time" — quote their exact
words back, give the counter, then give 2-3 options that all keep the test. Do not lecture.

| Excuse | Counter |
|---|---|
| "Too simple to test" | Simple code breaks too. The test takes 30 seconds. |
| "I already tested it manually" | Manual tests do not run in CI. They lie about regressions. |
| "I'll add the test after" | You will not. If you do, it passes trivially and proves nothing. |
| "It's just a prototype" | Prototypes ship. Test it, or write "will be rewritten" in the header. |
| "The change is obvious" | Obvious to whom, at 3 a.m., six months from now? |
| "No time" | Debugging the untested version costs 10x more time. |

---

## NASA Power of Ten

1. **Simple control flow.** No `goto`, no `setjmp`/`longjmp`, no unbounded recursion. Bound any
   recursion you need and document the bound.
2. **Bounded loops.** Every loop has a provable upper bound. Prefer a counted loop over
   `while True` with an internal break as the primary exit.
3. **Minimize dynamic allocation after initialization.** Allocate up front where latency or
   reliability matters. Reuse buffers on hot paths.
4. **Functions of 60 lines or fewer.** One screen, one function, one job. If you genuinely need
   more, document why and extract helpers anyway.
5. **Two or more meaningful assertions per function.** Preconditions, postconditions,
   invariants. Assertions are executable documentation.
6. **Minimum scope.** Declare variables close to use. Immutable by default. No module-level
   mutable state without strong justification.
7. **Validate inputs, check return values.** Every public function validates its parameters.
   Every caller checks what it gets back, including `Option`, `Result`, and error types. Silent
   failure is a bug.
8. **Limit metaprogramming.** No clever macros, decorators, reflection, or monkey-patching
   without a clear, local, documented win. Code should read linearly.
9. **Clear ownership of references.** One level of dereferencing per expression. Prefer values
   over references, and `Option`/`Result` over nullable pointers.
10. **Zero warnings at maximum strictness.** Lint and type-check at the strictest setting the
    toolchain supports. Warnings are errors in CI.

| Language | Minimum toolchain |
|---|---|
| TypeScript | `strict: true`, `noUncheckedIndexedAccess`, ESLint |
| Python | `ruff`, `mypy --strict`, `bandit` |
| Rust | `cargo clippy -- -D warnings`, `cargo deny`, `cargo audit` |
| Go | `go vet`, `staticcheck`, `golangci-lint` |
| C / C++ | `-Wall -Wextra -Wpedantic -Werror`, `clang-tidy`, ASan + UBSan |
| Java / Kotlin | Error Prone, SpotBugs, Detekt |

---

## DoD secure-coding baseline

Non-negotiable on anything touching untrusted input, secrets, or authentication.

1. **Input validation** — type, length, range, and format at every trust boundary.
2. **Output encoding** — context-appropriate for HTML, SQL, shell, LDAP, or JSON.
3. **Authentication and authorization** — verify identity, enforce least privilege, re-check on
   every request.
4. **Secrets management** — never hardcode. Use a vault, secret manager, or environment
   variable. Rotate. Never log.
5. **Cryptography** — vetted libraries only. No custom crypto. Modern algorithms, proper key
   management.
6. **Error handling** — fail closed. Never leak a stack trace or an internal path to a user.
7. **Logging and audit** — log security-relevant events. Never log secrets or PII.
8. **Memory safety** — prefer memory-safe languages. In C/C++ use bounds-checked APIs and
   sanitizers.
9. **Concurrency safety** — immutable by default, explicit synchronization, no shared mutable
   state without a documented lock.
10. **Supply chain** — pin dependencies, verify signatures, scan for CVEs, generate an SBOM.

---

## Flow: writing code

1. **RED** — Write the failing test. Its failure message is artifact prose, so `strict` binds
   it. Its name follows the identifier word rules; descriptive test names are exempt from the
   cluster cap. Run it. Confirm it fails for the right reason, not on a typo or a missing
   import. Show the output.
2. **GREEN** — Write the minimum code to pass. Nothing more. Check each new identifier against
   the word rules as you choose it, not afterward.
3. **REFACTOR** — Improve structure with tests green. Write docstrings and rationale comments
   to `clear`, and procedural comments to `strict`. Write error strings to `strict`. Re-run the
   tests after every structural change.
4. **COMMIT** — Write the message to `clear`, with an imperative subject line, and explain why
   rather than what.

## Flow: refactoring

Tests must exist before the refactor starts. A refactor without tests is a rewrite.

Behavior preservation includes names. STE word rules bind only concepts this change introduces.
Leave existing symbols alone, even when they break cluster length. Do not bundle a rename into
an unrelated refactor.

## When not to use this skill

- Throwaway scripts under about 20 lines with no maintenance expected.
- Exploratory prototypes — but write "will be rewritten before production" in the file header
  and link the follow-up ticket.
- Generated code you do not control. Fix the generator instead.
````

- [ ] **Step 2: Verify — a real write task**

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it.

Write a Python function that parses a duration string like "5m", "2h", or "300s" into an
integer number of seconds. Invalid input must raise a ValueError.

Work in /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t2/
and show me everything you produce.
```

**Pass — all six must hold:**
1. A failing test was written first and its failing output is shown.
2. The function is 60 lines or fewer.
3. It validates its input and has at least two meaningful assertions or explicit checks.
4. The `ValueError` message is 20 words or fewer, active voice, and names what the caller should
   do.
5. The docstring is written in `clear` — no idioms, no emoji, conclusion first.
6. No emoji anywhere in the produced file.

**Fail:** note which of the six failed, fix the corresponding section, re-run.

- [ ] **Step 3: Check the line count**

```bash
wc -l /home/code/development/ai/skills/mission-grade/SKILL.md
```

Expected: under 300 at this point. If it already exceeds 300, condense the Power of Ten and DoD
one-liners before starting Task 3 — Task 3 adds roughly 90 more lines.

- [ ] **Step 4: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/SKILL.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add condensed standards and the write/refactor flows

Power of Ten and the DoD secure-coding baseline as one-liners, the Iron
Law with its rationalization counters, and the TDD loop with each step's
prose surface bound to its mode.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `SKILL.md` — six gates, self-check, and communication rules

**Files:**
- Modify: `skills/mission-grade/SKILL.md` (append after the "When not to use this skill" section)

**Interfaces:**
- Consumes: the surface map and precedence from Task 1; the Power of Ten and DoD baseline
  numbering from Task 2.
- Produces: the six-gate review flow. Task 5 (`prose-gate.md`) expands Gate 6 and is referenced
  by name from here.

**Note on the spec:** the spec lists "the merged working checklist and self-check" as SKILL.md
contents. This task ships **one** list serving both roles. Two overlapping checklists is worse
than one — the second gets skipped, and then it is unclear which was authoritative.

- [ ] **Step 1: Append the review flow**

Append this content verbatim to `skills/mission-grade/SKILL.md`:

````markdown
---

## Flow: reviewing code

Walk all six gates in order. Collect every finding before you report any. A review that reports
one blocker when seven exist forces a second round per issue.

**Gate 1 — TDD discipline.** A new or changed test exists for every behavior change. Tests fail
without the change.

**Gate 2 — Power of Ten.** Functions over 60 lines. Unbounded loops or recursion. Bare public
functions with no validation or assertions. Unchecked return values. Variables at the broadest
scope. Metaprogramming without local justification.

**Gate 3 — Security baseline.** Untrusted input reaching SQL, a shell, the filesystem, `eval`,
or a deserializer without validation. A hardcoded secret. Custom cryptography. A new endpoint
with no authn/authz. Logs holding secrets or PII. **Each of these is a blocker.**

**Gate 4 — Maintainability.** Naming consistent with the codebase. Public APIs documented.
Error messages actionable. No dead or commented-out code. No `TODO` without a linked issue.

**Gate 5 — Build and CI.** Linters, type checkers, and static analyzers clean. Warnings still
errors. New dependencies reviewed for license, CVEs, and maintenance status.

**Gate 6 — Prose.** Artifact prose against the mode the surface map assigns it. Inspect:

- A warning or caution placed after the step it applies to
- A comment or docstring that contradicts the code
- An error string that hedges instead of naming an action
- A new identifier introducing a second term for a concept the module already names
- An idiom, metaphor, or emoji in shipped prose
- Undefined jargon on first use in a public docstring

Severity tracks harm, not rule count. A destructive warning sitting below its step is a
blocker. A 4-word noun cluster on a new helper is a nit. Full mapping and the not-a-finding
list: `references/prose-gate.md`.

### Report order

1. **Immediate-action items first.** If a secret is committed or an exploit is live, open with a
   ⚠️ callout telling the author exactly what to do right now — before they read anything else.
2. Gate 3 security blockers.
3. Remaining blockers, then majors, then minors, then nits.

Open the report by acknowledging what the code does well. State the gate result: 🔴 blocked when
a blocker exists, ✅ passed when none does.

### Every finding carries 2-3 options

Never just identify a problem. One option reads as an ultimatum. Four dilute the recommendation.

```
**[Severity] — [Rule citation]** — <the problem and its concrete impact, in one sentence>.

**Options:**
1. **<name>** (recommended): <what to do; why it is safest or simplest>
2. **<name>**: <alternative; when it is better>
3. **<name>**: <fallback; tradeoffs>

I'd lean toward option 1 because <reason>. Happy to draft it.
```

Cite the rule by name and number: Power of Ten #4, DoD baseline #4, Gate 6, CERT INTxx-C,
OWASP Ax, NIST SP 800-218 PW.x.

Be firm and friendly at once. State violations plainly — "this violates Power of Ten #4", not
"this might possibly be long". Do not soften a blocker into a suggestion. Do not apologize for
the standard. Assume good intent, acknowledge the work, and offer to help with the fix.

### Refusing a blocker

A blocker has no escape hatch. When a request would cross one:

```
**I will not <the specific action>.**
Rule: <citation>
Why this is a blocker: <one sentence on the concrete harm>.

Here's what I will do instead — pick one:
1. **<Option A>** (recommended): …
2. **<Option B>**: …
3. **<Option C>**: …

**What I will NOT do:** <restate the refused action, verbatim>.
```

Every option must satisfy the rule. Never list "do it anyway" as an option, even framed as "if
you insist". The answer to "if you insist" is to restate the refusal and offer to escalate to a
human decision-maker. You do not ship the violation.

---

## Self-check

This is the working checklist too. Run it against your draft before you send it, and run it
before you mark any task done. Do not narrate the check in your output.

1. Does every new identifier reuse the module's existing term for the concept?
2. Does any warning sit below the step it applies to?
3. Does every error string name an action the reader can take?
4. Is there an idiom, metaphor, or emoji anywhere in shipped prose?
5. Does every public function meet its 60-line limit, its assertion density, and its input
   validation?
6. Does every changed behavior have a test that failed first?
7. Is any secret hardcoded, and does any log line carry a secret or PII?
8. Is there dead code, an undocumented public API, or a `TODO` with no linked issue?
9. Do the linters and type checkers pass at their strictest setting?

If a check fails, fix it and re-run that check. Do not send output that fails a check.
````

- [ ] **Step 2: Verify — the dividing line, both directions (Scenario 2)**

This is the load-bearing test. It proves the principle the whole skill rests on.

Create the fixture:

```bash
mkdir -p /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3
cat > /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3/uploader.py <<'PY'
import requests

STRIPE_API_KEY = "sk_live_EXAMPLE_NOT_A_REAL_KEY"


def upload_report(path, customer_id):
    """Ships the report off to Stripe 🚀

    Fires and forgets — we don't wait around for the response.
    """
    with open(path) as f:
        data = f.read()
    return requests.post(
        "https://api.stripe.com/v1/reports",
        headers={"Authorization": "Bearer " + STRIPE_API_KEY},
        data={"customer": customer_id, "body": data},
    )
PY
```

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it.

Review this file and give me your report:
/tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3/uploader.py
```

**Pass — both halves must hold:**
- **Conversation side exempt:** the report opens with a ⚠️ callout about the live Stripe key,
  telling the author to revoke it now. The emoji is present. The finding prose explains the
  failure mode in normal explanatory sentences.
- **Artifact side bound:** the 🚀 in the docstring is flagged as a Gate 6 finding, and so is
  "Fires and forgets" as an idiom.

**Fail — the two diagnostic cases:**
- No ⚠️ in the report, or the finding prose chopped into 20-word telegram sentences → the skill
  is over-applying STE to the conversation side. Sharpen the dividing line.
- The docstring emoji or the idiom passes unflagged → Gate 6 is under-specified. Make the Gate 6
  inspection list more explicit.

- [ ] **Step 3: Verify — warning placement severity (Scenario 4)**

Create the fixture:

```bash
cat > /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3/reset.py <<'PY'
def reset_environment(env):
    # 1. Drop every table in the target schema.
    # 2. Re-run the migrations from scratch.
    # 3. Reseed the fixture data.
    # Note: this wipes all customer data in the target environment, so take a
    # backup first if you care about it.
    _drop_all_tables(env)
    _run_migrations(env)
    _seed_fixtures(env)
PY
```

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it.

Review this file and give me your report:
/tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3/reset.py
```

**Pass:** the misplaced destructive warning is reported as a **blocker**, with the fix being to
move it above step 1.
**Fail:** it is reported as a minor or nit, or not at all. Add an explicit line to Gate 6 that a
misplaced warning on a destructive step is a blocker, and re-run.

- [ ] **Step 4: Check the line count**

```bash
wc -l /home/code/development/ai/skills/mission-grade/SKILL.md
```

Expected: under 400. If over, condense the Power of Ten and DoD lists first — never the
dividing line, the surface map, or the precedence rules.

- [ ] **Step 5: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/SKILL.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add the six review gates, self-check, and refusal template

Adds Gate 6 for artifact prose alongside the five NASA/DoD gates, the
report ordering, the 2-3 options rule, and the blocker refusal template.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `references/ste-for-code.md`

This file is the actual intellectual content of the merge. Neither parent skill says what STE
word rules mean when the unit is an identifier or a log line.

**Files:**
- Create: `skills/mission-grade/references/ste-for-code.md`

**Interfaces:**
- Consumes: the surface map from Task 1.
- Produces: the identifier word-count rule (verb prefixes and type suffixes do not count toward
  the 3-word cap) and the error-message formula, both cited by `prose-gate.md` in Task 5.

- [ ] **Step 1: Write the file**

Write this content verbatim to `skills/mission-grade/references/ste-for-code.md`:

````markdown
# STE for Code

Companion to `skills/mission-grade/SKILL.md`. Load this when you need the word rules applied to
identifiers, user-facing strings, or comments, or when you need the substitution table.

ASD-STE100 was written for maintenance manuals. Three of its word rules transfer directly to
code, and this file defines what they mean when the unit is a symbol rather than a sentence.

---

## 1. Identifiers

Three rules apply. Nothing else does — sentence length and voice are meaningless for a name.

| Rule | In code |
|---|---|
| One word, one meaning | A word means the same thing everywhere in the module. Do not use `process` as both a noun and a verb in the same file. |
| Noun clusters of 3 or fewer | An identifier names at most 3 concept words. |
| Same word for the same thing | One term per concept per module. Do not alternate `file`, `document`, and `record` for one thing. |

**Counting concept words.** A leading verb (`get`, `set`, `build`, `parse`, `is`) and a
trailing type or role word do not count toward the 3. The concept words in between do. The
trailing words are exactly these: `List`, `Map`, `Set`, `Error`, `Handler`, `Config`. Treat
that list as closed — a word not on it counts.

- `getUserSessionToken` — verb `get`, concepts `user session token` = 3. Approved.
- `getMainLandingGearDoorActuatorSeal` — 6 concept words. Rejected.
- `parseInvoiceLineItemDiscountRuleSet` — 5 concept words. Rejected.

**Fixing an over-long name** — extract the inner concept into a type, so the name shortens
because the model got better:

> Rejected: `main_landing_gear_door_actuator_seal`
>
> Approved: a `LandingGearDoor` type with an `actuator_seal` attribute, reached as
> `door.actuator_seal`

**One term per concept:**

> Rejected: `save_file()`, `load_document()`, `delete_record()` — three names, one concept
>
> Approved: `save_file()`, `load_file()`, `delete_file()`

**These rules bind new concepts only.** If the module already calls it
`userAuthTokenExpiryPolicy`, a new function about that concept uses that term. Codebase
consistency beats cluster length. Never rename an existing symbol to satisfy this file.

**These rules never apply to** names fixed by something outside your control: external API
fields, protocol constants, database column names, framework hooks, and names in generated
code.

---

## 2. User-facing strings

Error, log, and CLI-help strings are `strict`. They are read by someone who is already stuck,
often at speed, often at 3 a.m.

**The formula: what failed, why, what to do.**

> Rejected: `Error: operation could not be completed successfully.`
>
> Approved: `Cannot write the config file. The directory /etc/app is read-only. Run the command
> with sudo, or set APP_CONFIG_DIR to a writable path.`

Rules that carry the most weight here:

- 20 words or fewer per sentence. Split a long message into short sentences, not clauses.
- Active voice. Name the actor. `The parser rejected line 12`, not `Line 12 was rejected`.
- Name an action the reader can take. A message with no action is a Gate 6 major.
- No hedging. `The file may not exist` is useless — check, then say which it is.
- No emoji. They render inconsistently across terminals, log aggregators, and CI output.
- No idioms. `Something went sideways` means nothing to a non-native reader or a translator.

> Rejected: `Oops! Something went wrong 😅 — the upload may have failed.`
>
> Approved: `The upload failed. The server returned status 507, which means it is out of
> storage. Retry after you free space, or contact support with request ID {id}.`

---

## 3. Comments and docstrings

Docstrings and rationale comments are `clear`. Procedural comments are `strict`.

**State the conclusion first.** The first sentence of a docstring says what the function does.
Reasoning, caveats, and history come after.

> Rejected: `Because the upstream API changed in v3 and we had trouble with the old retry
> logic, this now wraps the client and handles backoff.`
>
> Approved: `Sends a request with exponential backoff. Wraps the v3 client, which changed its
> retry semantics.`

**One instruction per sentence, imperative first, in procedural comments.**

> Rejected: `Stop the worker and drain the queue before you restart, then verify the offset.`
>
> Approved:
> ```
> # 1. Stop the worker.
> # 2. Drain the queue.
> # 3. Restart the worker.
> # 4. Make sure the offset is correct.
> ```

**A warning goes before the step it applies to, never after.** This is the single highest-value
rule in the whole skill. A caution placed below a destructive command is read too late.

> Rejected:
> ```
> # Drop the schema and rebuild it.
> # Note: this deletes all customer data.
> ```
>
> Approved:
> ```
> # WARNING: this deletes all customer data. Take a backup first.
> # Drop the schema and rebuild it.
> ```

**Never let a docstring contradict the code.** A wrong comment is worse than no comment, and
precedence rule 1 means accuracy beats every constraint in this file.

---

## 4. Substitutions for code prose

Apply to comments, docstrings, and user-facing strings. **Do not apply to identifiers that
mirror an external API** — if the library's method is `terminate()`, your wrapper says
`terminate()`.

| Rejected | Approved |
|---|---|
| ensure, verify, confirm, validate | make sure |
| utilize | use |
| commence, initiate | start |
| terminate, cease | stop |
| accomplish, execute, perform | do |
| obtain, acquire | get |
| require, necessitate | need |
| prior to | before |
| subsequent to, following | after |
| in order to | to |
| in the event that | if |
| is able to, has the ability to | can |
| due to the fact that | because |
| approximately | about |
| additional | more |

**Delete rather than replace** — these add length without meaning: `basically`, `essentially`,
`actually`, `really`, `very`, `quite`, `simply`, `just`, `obviously`, `clearly`, `of course`,
`it should be noted that`.

This is a working aid built from commonly cited substitutions. It is **not** the ASD-STE100
dictionary, which holds roughly 900 entries and is ASD's copyrighted content. For the full
table, see `skills/nfc/references/style-rules.md` section 5 if that skill is present. For the
authoritative list, obtain the official specification free of charge from
<https://www.asd-ste100.org/STE_downloads.html>.

---

## 5. What STE never touches

- Code syntax, keywords, and operators.
- Quoted or reproduced material — code you cite in a review, command output, log excerpts.
- Names fixed outside your control: external APIs, protocol constants, database columns.
- Existing identifiers, unless the user asked for a rename.
- Test fixture data and sample payloads.
````

- [ ] **Step 2: Verify — no collateral renames (Scenario 3)**

Create the fixture:

```bash
mkdir -p /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t4
cat > /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t4/billing.py <<'PY'
def get_customer_subscription_billing_cycle_anchor(customer):
    return customer.anchor


def compute_customer_subscription_proration_credit_amount(customer, days):
    anchor = get_customer_subscription_billing_cycle_anchor(customer)
    return customer.plan.rate * days / anchor.period_days
PY
```

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and follow it. It may point you
at companion files; read those if you need them.

In this file, add a function that returns the number of whole days left in a customer's
current billing period:
/tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t4/billing.py

Show me the resulting file.
```

**Pass:** both existing functions keep their original names despite exceeding 3 concept words,
and the new function reuses the module's existing terms (`customer`, `subscription`, `billing`)
rather than introducing a synonym such as `client` or `account`.
**Fail:** any existing symbol renamed, or a rename proposed unprompted. Strengthen the
"bind new concepts only" paragraph and re-run.

- [ ] **Step 3: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/references/ste-for-code.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add ste-for-code reference

Defines what the STE word rules mean when the unit is an identifier or a
log line: concept-word counting that excludes verb prefixes and type
suffixes, the error-message formula, and code-prose substitutions.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `references/prose-gate.md`

**Files:**
- Create: `skills/mission-grade/references/prose-gate.md`

**Interfaces:**
- Consumes: the Gate 6 inspection list from Task 3; the concept-word rule and error-message
  formula from Task 4.
- Produces: the severity mapping cited by Gate 6 in `SKILL.md`.

- [ ] **Step 1: Write the file**

Write this content verbatim to `skills/mission-grade/references/prose-gate.md`:

````markdown
# Gate 6 — The Prose Gate

Companion to `skills/mission-grade/SKILL.md`. Load this when reviewing, to classify a prose
finding or to decide whether something is a finding at all.

Gate 6 inspects prose that ships in the repository. It never inspects your own review output.

---

## Severity mapping

Severity tracks harm to a reader who trusts the prose. It does not track how many rules the
line breaks.

### Blocker — must fix before merge

| Finding | Why |
|---|---|
| A warning or caution placed after a destructive step | The reader runs the command before reaching the warning. This is the failure mode the rule exists to prevent. |
| A comment or docstring that contradicts the code | A wrong comment is worse than no comment. Callers trust it and build on a false premise. |
| An error message instructing an unsafe action | The message causes the harm it was meant to prevent. |
| A secret, token, or PII value in a log string | Also DoD baseline #7. Report it under Gate 3 with the immediate-action callout. |

### Major — fix before merge

| Finding | Why |
|---|---|
| A public docstring that leaves jargon undefined on first use | Excludes exactly the reader who most needs the doc. |
| An error message that states a failure and no action | The reader is stuck with no next step. |
| A new identifier introducing a second term for an existing concept | Vocabulary drift compounds. Every later reader pays. |

### Minor — fix if easy

- A procedural comment over the 20-word cap
- Passive voice where the actor is known
- A new identifier with 4 concept words
- Hedging with no stated cause
- An emoji in a user-facing string
- An idiom or metaphor in a user-facing string

### Nit — optional

- A substitution-table word (`utilize` for `use`)
- An emoji in an internal comment or docstring
- An idiom or metaphor in an internal comment or docstring
- A dropped article
- A filler word (`basically`, `simply`, `just`)

---

## Not a finding

Do not report any of these. A review that flags them trains the author to ignore Gate 6, which
costs you the blockers too.

- **Existing identifiers** that exceed the concept-word cap, when this change did not introduce
  them. Consistency beats cluster length.
- **Names fixed outside the author's control** — external API fields, protocol constants,
  database columns, framework hooks.
- **Quoted or reproduced material** — code cited from elsewhere, log excerpts, command output,
  sample payloads.
- **Generated files.** Report the generator instead, once.
- **Test fixture strings and sample data.** Deliberately messy input is the point.
- **Your own review prose.** Findings, citations, and callouts are conversation side and exempt.
- **A qualifier that survived a word cap.** Precedence rule 1 says accuracy wins. A longer,
  correct sentence is not a finding.
- **An assertion message that names the required condition.** `"limit must be positive"` states
  what the caller must do. Assertions address a programmer who broke an invariant, not an end
  user, so the what/why/what-to-do formula does not bind them.
- **A descriptive test name.** Test names carry information a reader needs at a glance. The
  cluster cap does not apply to them.

---

## Finding template

Gate 6 findings use the same shape as every other gate. Cite the rule, state the concrete
failure mode, give 2-3 options, mark the recommendation.

```
**Blocker — Gate 6 (warning placement)** — the caution about wiping customer data sits below
the three steps it applies to, so a reader following the steps in order runs the destructive
command before reading it.

**Options:**
1. **Move the warning above step 1 (recommended):** one-line change, matches the rule, and the
   reader cannot miss it.
2. **Move it above step 1 and add a confirmation prompt:** better if this runs interactively in
   production, since the comment only protects readers of the source.
3. **Move it to the function docstring:** cheapest to read at the call site, but it is lost to
   anyone editing the body.

I'd take option 1 now and open a ticket for option 2 if this is ever run by hand.
```

---

## Review checklist

Run in order. Stop only when all six are answered.

1. Is any warning below the step it applies to? Is that step destructive?
2. Does any comment or docstring state something the code does not do?
3. Does every error string name an action?
4. Does any new identifier introduce a second term for a concept the module already names?
5. Is there an idiom, metaphor, or emoji in shipped prose?
6. Is jargon undefined on first use in a public docstring?
````

- [ ] **Step 2: Verify — severity differentiation**

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md and
/home/code/development/ai/skills/mission-grade/references/prose-gate.md, and follow them.

Assign a severity to each of these review findings. Answer as a list of six severities with
one sentence of reasoning each. Give no other commentary.

A. A comment reading "delete the volume" sits above a note saying this destroys the only
   replica.
B. A public function `resolve_tenant()` has no docstring.
C. A new helper is named `build_tenant_billing_account_summary_row`.
D. A docstring says the function returns None on failure; it actually raises.
E. A comment reads "utilize the cached client where possible".
F. An existing 5-word function name that this pull request did not touch.
```

**Pass:** A = blocker, B = major, C = minor, D = blocker, E = nit, F = not a finding.
**Fail:** any mismatch, especially F being reported. Sharpen the corresponding row and re-run.

- [ ] **Step 3: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/references/prose-gate.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add the prose gate reference

Maps STE violations onto blocker/major/minor/nit by harm rather than
rule count, and defines an explicit not-a-finding list so Gate 6 does not
train authors to ignore it.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: `references/examples.md`

**Files:**
- Create: `skills/mission-grade/references/examples.md`

**Interfaces:**
- Consumes: everything from Tasks 1-5.
- Produces: nothing other files depend on. This is the last content file.

Every code sample in this file is artifact side. Its comments, docstrings, and error strings
must pass the skill's own self-check — this file is the demonstration, so a violation in it
teaches the violation.

- [ ] **Step 1: Write the file**

Write this content verbatim to `skills/mission-grade/references/examples.md`:

````markdown
# Worked Examples

Companion to `skills/mission-grade/SKILL.md`. Three end-to-end runs: one write, one refactor,
one review.

---

## Example 1 — Writing a feature

**Request:** "Add a rate limiter to the upload endpoint. 10 uploads per minute per tenant."

**RED.** The failure message is artifact prose, so `strict` binds it. The test's name follows
the identifier word rules; descriptive test names are exempt from the cluster cap.

```python
def test_rate_limiter_blocks_the_eleventh_upload_in_one_minute():
    limiter = RateLimiter(limit=10, window_seconds=60)
    for _ in range(10):
        assert limiter.allow("tenant-a") is True
    assert limiter.allow("tenant-a") is False, "The limiter must refuse the 11th upload."
```

Run it. Show the output:

```
E   NameError: name 'RateLimiter' is not defined
```

That is a failure for the right reason. A test that fails on a typo proves nothing.

**GREEN.** Minimum code. Identifiers checked as they are chosen: `RateLimiter`, `allow`,
`window_seconds` — each 1 to 2 concept words, and `tenant` is already the module's term.

```python
class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        assert limit > 0, "limit must be positive"
        assert window_seconds > 0, "window_seconds must be positive"
        self._limit = limit
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def allow(self, tenant: str) -> bool:
        assert tenant, "tenant must not be empty"
        now = time.monotonic()
        cutoff = now - self._window_seconds
        recent = [t for t in self._hits.get(tenant, []) if t > cutoff]
        if len(recent) >= self._limit:
            self._hits[tenant] = recent
            return False
        recent.append(now)
        self._hits[tenant] = recent
        assert len(recent) <= self._limit, "recent must not exceed the limit"
        return True
```

Power of Ten as applied: bounded loop (rule 2), both functions under 60 lines (rule 4), two or
more assertions each (rule 5), inputs validated (rule 7).

**REFACTOR.** Docstrings in `clear` — conclusion first, no idioms, no emoji:

```python
class RateLimiter:
    """Limits how many attempts one tenant can make in a sliding time window.

    `limit` is the maximum number of attempts. `window_seconds` is the length of
    the window in seconds. Both must be positive.
    """

    def allow(self, tenant: str) -> bool:
        """Reports whether an upload is permitted, and records it only when it is.

        Returns True when the tenant made fewer than `limit` attempts in the last
        `window_seconds`. Returns False otherwise, and does not record the attempt.

        The window slides. It does not reset on a fixed boundary.
        """
```

The error string the endpoint returns is `strict` — what failed, why, what to do:

```python
raise RateLimitExceeded(
    f"The limiter refused the upload. Tenant {tenant} reached {limit} uploads "
    f"in {window_seconds} seconds. Retry after {retry_after} seconds."
)
```

**COMMIT.** `clear`, imperative subject, explains why:

```
feat(uploads): limit each tenant to 10 uploads per minute

A single tenant could saturate the upload workers and delay every other
tenant. The limiter uses a sliding window, so a burst at a minute
boundary cannot pass twice the limit.
```

---

## Example 2 — Refactoring

**Request:** "Split this 90-line handler up."

The module already uses these terms: `subscription`, `proration`, `invoice`. Existing names
include `compute_customer_subscription_proration_credit_amount` — 5 concept words, over the cap.

**What the skill does:** extracts by phase, giving each helper a name built from the module's
existing terms.

```python
def handle_subscription_change(request):
    """Computes the invoice for a subscription change."""
    change = _parse_subscription_change(request)
    credit = _compute_proration_credit(change)
    invoice = _build_invoice(change, credit)
    return invoice
```

**What the skill does not do:** rename
`compute_customer_subscription_proration_credit_amount`. It exceeds the concept-word cap, and
it is untouched by this change. Consistency beats cluster length, and a rename is its own pull
request. The skill does not mention the rename as an option unless the user asks.

Tests exist before any of this moves. A refactor without tests is a rewrite.

---

## Example 3 — Reviewing

**Input:** a pull request adding an admin endpoint, with a hardcoded token and a docstring
reading `"Nukes the tenant's data 💥 — no takebacks!"`.

**The report.** Conversation side, so emoji are required and the prose explains normally:

> Nice work threading the tenant scope through the deletion path — the cascade order is right,
> and the integration test covers the orphaned-rows case properly.
>
> ⚠️ **Do this first:** `ADMIN_TOKEN = "at_live_9f2b…"` is committed at `admin/routes.py:14`.
> That token is in git history permanently and must be treated as compromised. Revoke it at the
> provider now, before reading the rest of this review.
>
> 🔴 **Gate status: BLOCKED** — 2 blockers, 1 major, 1 nit.
>
> **Blocker — DoD baseline #4 (secrets management)** — the admin token is hardcoded, so anyone
> with repository read access holds production admin rights.
>
> **Options:**
> 1. **Rotate, then load from the environment (recommended):** revoke now, issue a new token,
>    read `ADMIN_TOKEN` at startup, and fail fast when it is missing.
> 2. **Rotate, then pull from your secret manager:** better if you already run Vault or AWS
>    Secrets Manager, since it gets you rotation for free.
> 3. **Rotate, then use a gitignored env file:** cheapest and weakest. Local development only.
>
> Option 1 regardless — the revoke step cannot wait for the design discussion.
>
> **Blocker — Gate 6 (contradictory docstring)** — the docstring says the deletion is
> irreversible, but the implementation writes to `deleted_tenants` and the runbook restores from
> it. A caller reading this docstring will refuse a legitimate restore request.
>
> **Options:**
> 1. **Correct the docstring (recommended):** state that rows move to `deleted_tenants` and
>    name the retention window.
> 2. **Correct it and link the restore runbook:** better if support staff read this file.
> 3. **Make the code match the docstring:** only if the retention behavior was unintended.
>
> **Major — Power of Ten #7 (input validation)** — `delete_tenant` does not validate
> `tenant_id` before it reaches the query builder. … [options follow]
>
> **Nit — Gate 6 (emoji and idiom in shipped prose)** — 💥 and "no takebacks" render
> inconsistently across terminals and do not survive translation.

Note the split. The ⚠️ and 🔴 in the report are required. The 💥 in the docstring is a finding.
Same document, opposite rules, because one is the conversation and one is the artifact.
````

- [ ] **Step 2: Verify — the examples pass the skill's own self-check**

Dispatch a fresh subagent with this exact prompt:

```
Read /home/code/development/ai/skills/mission-grade/SKILL.md,
/home/code/development/ai/skills/mission-grade/references/ste-for-code.md, and
/home/code/development/ai/skills/mission-grade/references/prose-gate.md. Follow them.

Now review the code samples, docstrings, comments, and error strings inside
/home/code/development/ai/skills/mission-grade/references/examples.md as if they were
production code. Report every Gate 6 finding you can support.

Treat the surrounding explanatory prose and the sample review report as out of scope — review
only the code blocks and the strings inside them.
```

**Pass:** no blocker or major findings against the code samples.
**Fail:** any blocker or major. Fix the sample, not the gate. A demonstration file that violates
the standard teaches the violation.

- [ ] **Step 3: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/references/examples.md
git commit -m "$(cat <<'EOF'
docs(mission-grade): add three worked examples

One write, one refactor, one review. The review example shows required
emoji in the report alongside a flagged emoji in a docstring — the
dividing line demonstrated inside a single document.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Optional-depth pointers, attribution, and README registration

**Files:**
- Modify: `skills/mission-grade/SKILL.md` (append the final two sections)
- Modify: `README.md` (skill card + badge)

**Interfaces:**
- Consumes: all four skill files.
- Produces: the finished, registered skill.

- [ ] **Step 1: Append the pointers and attribution to `SKILL.md`**

Append this content verbatim to `skills/mission-grade/SKILL.md`:

````markdown
---

## Going deeper

This skill is self-contained. Everything above works with no other file loaded. The files below
add depth when a task needs it. **If a path does not exist, say so in one line and continue with
what you have** — never block on a missing optional file.

**This skill's own references** — always present:

| File | Load when |
|---|---|
| `references/ste-for-code.md` | Naming a new concept, writing a user-facing string, or applying the substitution table |
| `references/prose-gate.md` | Classifying a Gate 6 finding, or deciding whether something is a finding |
| `references/examples.md` | You want a worked end-to-end run before starting |

**Sibling skills** — optional, may be absent:

| Source | Provides |
|---|---|
| `skills/nfc/` | The full ASD-STE100 substitution table, `[STE]` versus `[NFC]` rule provenance, and the list of STE rules this skill does not implement |
| `skills/applying-nasa-dod-coding-standards/` | Full gate prose, the complete rationalization-counter tables, and the long-form refusal template |
| `skills/nasa-dod-code-review/` | The formal report workflow — CODEOWNERS setup, P0-P3 severity, and a written report under `reports/`. Load this only when the user explicitly asks for a written report file. |

If the user has obtained the official ASD-STE100 specification and saved it at
`skills/nfc/references/ASD-STE100.pdf`, check word choices against it in `strict` mode. It is
not vendored with this repository.

---

## Scope

This skill does not:

- Change facts, conclusions, or recommendations to make them simpler than they are.
- Remove real uncertainty. If something is genuinely unknown, say so plainly and say why.
- Rewrite code, commands, output, or quoted material. Reproduce those exactly.
- Rename existing identifiers as a side effect of unrelated work.
- Certify ASD-STE100 conformance. It improves clarity. Do not claim more than that.

---

## Attribution

The mechanical writing rules are derived from ASD-STE100 Simplified Technical English, Issue 9
(January 2025), copyright ASD (AeroSpace and Defence Industries Association of Europe),
maintained by the STE Maintenance Group. This skill implements the writing rules only. It does
not reproduce the ASD-STE100 approved-word dictionary, which is ASD's copyrighted content.
Obtain the official specification, including the dictionary, free of charge from
<https://www.asd-ste100.org/STE_downloads.html>.

This skill is an independent work and is not endorsed by or affiliated with ASD or the STEMG.

Engineering standards derive from Holzmann, G. J. (2006), *The Power of Ten: Rules for
Developing Safety-Critical Code*, NASA/JPL, IEEE Computer 39(6), 95-99; NIST SP 800-218
(Secure Software Development Framework); the DISA Application Security and Development STIG;
and the CERT Secure Coding Standards.
````

- [ ] **Step 2: Verify — ships alone (Scenario 5)**

This is the second load-bearing test. It proves the architecture choice.

```bash
rm -rf /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo
mkdir -p /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo
cp -r /home/code/development/ai/skills/mission-grade \
      /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo/
ls -R /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo
```

Expected: `mission-grade/SKILL.md` plus `mission-grade/references/` with three files, and no
sibling skill directories anywhere.

Dispatch a fresh subagent with this exact prompt:

```
Read /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo/mission-grade/SKILL.md
and follow it.

Write a Python function that reads a JSON config file and returns the parsed dict. A missing
file, unreadable file, or malformed JSON must each raise a distinct, specific exception.

Work in that same directory and show me everything you produce.
```

**Pass:** the task completes fully. A test was written first. If the agent mentions a sibling
skill at all, it notes the absence in a line or two and carries on.
**Fail:** the agent stalls, reports it cannot proceed, or asks the user to supply a missing
file. Rewrite the offending pointer as optional and re-run.

- [ ] **Step 3: Add the README skill card**

In `README.md`, insert this card immediately after the NFC card (which ends at the `| **Portable** | ... |` row, currently line 243) and before the `---` that follows:

```markdown

### 🛰️ [Mission Grade](skills/mission-grade/)

Applies NASA/DoD engineering standards to the code and [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/) to the prose that ships with it — comments, docstrings, error messages, identifiers, commit messages — from a single trigger, with no need to name two skills on every request.

The two standards contradict each other in specific places, and one line resolves all of them: **STE governs the artifact, NASA/DoD governs the conversation about the artifact.** A review of the same file therefore carries a required ⚠️ callout for a leaked key while flagging an emoji in a docstring three lines below it.

| | |
|---|---|
| **Trigger** | "refactor this" · "implement X" · "review this code" · "mission grade" · any production code work |
| **Code** | Power of Ten · DoD secure-coding baseline · TDD Iron Law — no production code without a failing test |
| **Prose** | Procedural comments and error strings `strict` · docstrings and commits `clear` · identifiers by word rules |
| **Review** | Six gates — the five NASA/DoD gates plus a prose gate, severity by harm rather than rule count |
```

- [ ] **Step 4: Bump the skill-count badge**

In `README.md` line 9, change `badge/skills-10-brightgreen` to `badge/skills-11-brightgreen`.

Verify:

```bash
grep -n "badge/skills-" /home/code/development/ai/README.md
```

Expected: one line, reading `skills-11-brightgreen`.

- [ ] **Step 5: Final check — line count and no stray placeholders**

```bash
cd /home/code/development/ai
wc -l skills/mission-grade/SKILL.md skills/mission-grade/references/*.md
grep -rn "TBD\|TODO\|FIXME\|XXX" skills/mission-grade/ || echo "CLEAN"
```

Expected: `SKILL.md` under 400 lines, and `CLEAN` from the grep.

- [ ] **Step 6: Commit**

```bash
cd /home/code/development/ai
git add skills/mission-grade/SKILL.md README.md
git commit -m "$(cat <<'EOF'
feat(mission-grade): add optional-depth pointers, attribution, and README entry

Sibling skills are named as optional depth with explicit instructions to
continue when absent, so the directory works lifted out of the repo.
Registers the skill in the README and bumps the badge to 11.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
EOF
)"
```

---

## Verification Summary

All six spec scenarios, and where each is exercised:

| # | Scenario | Task | Step |
|---|---|---|---|
| 1 | Auto-activation with no skill named | 1 | 3 |
| 2 | Dividing line, both directions | 3 | 2 |
| 3 | No collateral renames | 4 | 2 |
| 4 | Warning placement is a blocker | 3 | 3 |
| 5 | Ships alone | 7 | 2 |
| 6 | Accuracy escape hatch | 1 | 5 |

Scenarios 2 and 5 are load-bearing. Scenario 2 tests the principle the skill is built on.
Scenario 5 tests the portability property that drove the architecture. If either fails and
cannot be fixed by tightening wording, stop and revisit the spec rather than weakening the
pass condition.

Three additional checks beyond the spec's six: surface classification (Task 1 Step 4), a real
write task (Task 2 Step 2), severity differentiation (Task 5 Step 2), and the examples
dogfooding check (Task 6 Step 2).

## Cleanup

After Task 7 passes, remove the scratch fixtures:

```bash
rm -rf /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t2 \
       /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t3 \
       /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-t4 \
       /tmp/claude-1000/-home-code-development-ai/ca9fb2e8-45b4-4f02-bdcf-3888a309df06/scratchpad/mg-solo
```

Nothing under `skills/mission-grade/` or `docs/` is temporary. Leave those in place.
