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
| Identifiers | STE word rules only | see below |
| Error, log, and CLI-help strings | STE | `strict` |
| Commit messages, PR descriptions | STE | `clear` |
| Review findings, rule citations, callouts, gate status, option lists | NASA/DoD | exempt |
| Chat replies about the work | NASA/DoD | exempt |

The table is fixed. Do not offer to change it, and do not adjust it on request — point the user
at `skills/nfc/` if they want freely selectable modes.

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
