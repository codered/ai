# mission-grade — Design

**Date:** 2026-08-02
**Status:** Approved for planning

## Summary

`mission-grade` is a superset skill that applies NASA/DoD engineering standards to code and
ASD-STE100 mechanical writing rules to the prose that ships with it — from a single trigger.

Today a user must invoke two skills by name to get both. This skill removes that friction: it
auto-activates on production code work, carries the common path in one file, and loads deeper
material from its own references or the sibling skills only when needed.

It covers writing new code, refactoring existing code, and reviewing code.

## Problem

The repository already contains the raw material, split across three skills:

| Skill | Provides |
|---|---|
| `applying-nasa-dod-coding-standards` | Power of Ten, DoD secure-coding baseline, TDD Iron Law, five review gates, 2–3-options communication rule |
| `nasa-dod-code-review` | Formal review workflow: P0–P3 severity, gate logic, `reports/` output, CODEOWNERS setup |
| `nfc` | ASD-STE100-derived writing filter: three modes, countable rule table, self-check, substitution table |

Two problems follow from the split:

1. **Invocation friction.** Getting both standards requires naming both skills on every request.
2. **Undefined interaction.** The two standards contradict each other in specific, identifiable
   places, and nothing currently resolves those contradictions. NFC's Scope section explicitly
   excludes code, which is precisely where this skill needs it to apply.

## Core principle

**STE governs the artifact. NASA/DoD governs the conversation about the artifact.**

If it is committed to the repository, STE binds it. If it is the skill communicating with the
user — a finding, a rule citation, a gate result — NASA/DoD's communication rules bind it and
STE does not apply.

This single line resolves every known conflict between the two standards.

## Surface map

| Surface | Governed by | STE mode |
|---|---|---|
| Procedural comments (how-to, setup steps) | STE | `strict` |
| Rationale comments (why a decision was made) | STE | `clear` |
| Docstrings, module headers | STE | `clear` |
| Identifiers | STE word rules 4.1, 4.2, 4.5 only | n/a |
| Error, log, and CLI-help strings | STE | `strict` |
| Commit messages, PR descriptions | STE | `clear` |
| Review findings, rule citations, callouts, gate status, option lists | NASA/DoD | exempt |
| Chat replies about the work | NASA/DoD (firm yet friendly) | exempt |

The mode table is fixed. It is not user-overridable in v1.

**Distinguishing procedural from rationale comments:** a comment is procedural if it tells the
reader to do something — setup steps, an ordering the caller must obey, a manual recovery
procedure. It is rationale if it explains why the code is as it is. When a comment does both,
split it: the procedural part becomes a numbered list in `strict`, the rationale stays in prose
in `clear`. When the split is not worth it, apply `clear` and keep any instruction on its own
line.

Mode definitions (`standard` / `clear` / `strict`) and the full rule table are in
`skills/nfc/SKILL.md`. `mission-grade` restates the countable subset that applies to code
artifacts so the common path needs no additional file load.

## Precedence rules

Applied in this order:

1. **Accuracy wins over everything.** If an STE constraint would make a comment, docstring, or
   error message wrong, misleading, or falsely certain, keep it accurate and state in one line
   which constraint was relaxed and why. This applies to accuracy only. It is never an escape
   hatch for convenience, brevity, or effort.
2. **NASA/DoD wins over STE.** Wherever the two give conflicting instructions on the same
   output, follow NASA/DoD.
3. **STE binds everything else** it is assigned in the surface map.

### Resolved conflicts

**Emoji.** The NASA/DoD standard mandates a warning callout for immediate-action items and a
status marker for a blocked gate. STE rule 4.7 prohibits emoji. Resolution: emoji are required
in review output and callouts (conversation side) and prohibited in comments, docstrings, and
user-facing strings (artifact side).

**Explanation versus sentence caps.** "Cite the rule, state the failure mode, give 2–3 options
with tradeoffs" is inherently explanatory prose, and `strict` caps sentences at 20 words and
restricts hedging. Resolution: findings and tradeoff prose are on the conversation side, so the
caps never apply to them. A genuinely conditional tradeoff is stated as conditional.

**Identifier naming versus codebase consistency.** STE 4.2 caps noun clusters at 3 words and
4.5 requires one term per concept. NASA/DoD Gate 4 requires naming consistent with the
surrounding codebase. Resolution: Gate 4 wins. STE word rules apply only to concepts the
current change introduces. The skill does not rename existing symbols to satisfy cluster
length, and does not propose such renames unless the user asks. A sweeping rename is its own
pull request.

**Quoted material.** Carried over from NFC unchanged: quoted and reproduced material is never
rewritten. STE applies to prose the skill authors, never to code or text it cites.

## Architecture

Approach: **self-contained hot path, delegated depth.**

`SKILL.md` handles a normal write, refactor, or review with no additional file loaded. Deeper
material lives in the skill's own `references/`. Sibling skills are named as optional depth and
are never required — the directory functions when lifted out of the repository alone.

This mirrors the portability property `skills/nfc` gained in commit `7df8a1f`.

### Layout

```
skills/mission-grade/
├── SKILL.md
└── references/
    ├── ste-for-code.md
    ├── prose-gate.md
    └── examples.md
```

### SKILL.md contents

- Frontmatter: `name`, `description` written to auto-trigger on production code work
- The artifact/conversation dividing line
- The surface map table
- Power of Ten as ten one-line rules
- DoD secure-coding baseline as ten one-line rules
- The TDD Iron Law
- The countable STE rules that apply to code artifacts — the applicable subset, not all 53
- The three precedence rules and the resolved conflicts
- Six review gates
- The merged working checklist and self-check
- The 2–3-options rule and the refusal-template skeleton
- Pointers to `references/` and to sibling skills, each stating what it provides and when the
  load is worth it

Target length is approximately 300 lines, in line with the sibling skills
(`applying-nasa-dod-coding-standards` is 442 lines, `nfc` is 265).

### references/ste-for-code.md

The material neither parent skill contains: what STE word rules 4.1, 4.2, and 4.5 mean when the
unit is an identifier, a log line, or a docstring, with before/after pairs for each. Includes
approximately 15 high-frequency word substitutions specific to code prose. Points to
`skills/nfc/references/style-rules.md` section 5 for the full table.

### references/prose-gate.md

Gate 6 in detail: what to inspect, how an STE violation maps onto blocker / major / minor / nit,
and the finding template. Severity tracks harm, not rule count.

### references/examples.md

Three end-to-end worked examples: one write, one refactor, one review.

### Optional depth

Each pointer states what it provides and when to load it. Absence is reported as a stated
absence, never a broken load.

| Source | Provides |
|---|---|
| `skills/nfc/references/style-rules.md` | Full substitution table, `[STE]`/`[NFC]` rule provenance, rules NFC does not implement |
| `skills/applying-nasa-dod-coding-standards/SKILL.md` | Full gate prose, rationalization-counter tables, complete refusal template |
| `skills/nasa-dod-code-review/SKILL.md` | Formal report workflow, loaded only when the user explicitly asks for a written report |
| `skills/nfc/references/ASD-STE100.pdf` | The official approved-word dictionary, if the user has obtained and placed it. Not vendored — see the attribution section |

## Activation

The `description` field triggers on any write, refactor, or review of production code — the same
trigger surface `applying-nasa-dod-coding-standards` has today. The skill name also works as a
manual trigger.

**Do not use for:** throwaway scripts under approximately 20 lines with no maintenance
expectation, and exploratory prototypes — which get the header line "will be rewritten before
production" plus a link to the follow-up ticket, as the parent skill requires.

## Behavior

### Write

Test-driven development governs the loop. STE governs the prose produced inside it.

1. **RED** — Write the failing test. The test name and its failure message are artifact prose
   and are bound by STE. Confirm the test fails for the right reason. Show the failing output in
   the reply; the reply is conversation and is exempt.
2. **GREEN** — Write the minimum code to pass. Check new identifiers against the word rules as
   they are chosen.
3. **REFACTOR** — Improve structure with tests green. Write docstrings and comments to `clear`.
   Write error strings to `strict`.
4. **Commit** — Write the commit message to `clear`, with an imperative subject line.

### Refactor

Tests must exist before the refactor starts. A refactor without tests is a rewrite.

Behavior preservation includes names. STE word rules bind only concepts the change introduces.
Existing symbols are left alone.

### Review

Walk all six gates in order. Collect every finding before reporting any.

1. TDD discipline
2. Power of Ten compliance
3. Security baseline
4. Maintainability
5. Build and CI
6. **Prose gate**

Gate 6 inspects:

- A warning or caution placed after the step it applies to
- A comment or docstring that contradicts the code
- An error string that hedges instead of naming an action
- A new identifier that introduces a second term for a concept the module already names
- An idiom, metaphor, or emoji in shipped prose
- Undefined jargon on first use

Report findings NASA/DoD-style: cite the rule, state the failure mode, give three options, mark
the recommendation.

Report order follows the parent skill: immediate-action items first, then security blockers,
then remaining blockers, majors, minors, and nits.

### Self-check

Run against the draft before output. Kept short so that it is actually run.

1. Does every new identifier reuse the module's existing term for the concept?
2. Does any warning sit below the step it applies to?
3. Does every error string name an action?
4. Is there an idiom, metaphor, or emoji in shipped prose?
5. Does every public function meet its 60-line limit, assertion density, and input validation?
6. Does every changed behavior have a test that failed first?

## Verification

No runtime code, so verification is scenario-based. Each scenario targets one design claim and
has an observable pass/fail.

| # | Scenario | Pass condition |
|---|---|---|
| 1 | "Refactor this module", no skill named | The skill activates on its own |
| 2 | Review code containing both a committed secret and an emoji in a docstring | Output contains a warning callout for the secret (conversation side exempt) **and** flags the docstring emoji (artifact side bound) |
| 3 | Refactor a file whose existing identifiers exceed 3-word clusters | Existing identifiers are unchanged; word rules apply only to newly introduced symbols |
| 4 | Code documenting a destructive step with the caution below it | Gate 6 returns a blocker, not a nit |
| 5 | Copy `skills/mission-grade/` into a bare directory with no siblings, then run a write task | The skill works; optional-depth pointers degrade to a stated absence, not a broken load |
| 6 | A statement where `strict` would flatten a genuine conditional into false certainty | The skill keeps it accurate and names the relaxed constraint in one line |

Scenarios 2 and 5 are load-bearing. Scenario 2 tests the principle the skill is built on.
Scenario 5 tests the portability property that drove the architecture.

## Out of scope for v1

- User-overridable mode tiers. The surface map is fixed.
- Automatic conformance certification. As NFC already states, this improves clarity; it does not
  certify ASD-STE100 conformance, and no output should claim that it does.
- Bundling the ASD-STE100 approved-word dictionary. It remains user-obtained and not vendored.
- Replacing or deprecating the three existing skills. They stay, and remain independently
  usable.

## Attribution

The mechanical writing rules are derived from ASD-STE100 Simplified Technical English, Issue 9
(January 2025), copyright ASD (AeroSpace and Defence Industries Association of Europe),
maintained by the STE Maintenance Group. This skill implements the writing rules only. It does
not reproduce the approved-word dictionary, which is ASD's copyrighted content. Obtain the
official specification free of charge from <https://www.asd-ste100.org/STE_downloads.html>.

`mission-grade` is an independent work and is not endorsed by or affiliated with ASD or the
STEMG.

Engineering standards derive from Holzmann, G. J. (2006), *The Power of Ten: Rules for
Developing Safety-Critical Code*, NASA/JPL; NIST SP 800-218 (SSDF); DISA Application Security
and Development STIG; and CERT Secure Coding Standards.
