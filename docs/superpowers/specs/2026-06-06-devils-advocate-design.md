# Devil's Advocate Skill — Design Spec
**Date:** 2026-06-06
**Status:** Approved

---

## Overview

A standalone, agent-agnostic skill that challenges a request, design, plan, or position by actively hunting for logical gaps, hidden assumptions, missed edge cases, and unconsidered counter-framings. Tone is friendly yet firm, calibrated to the stakes of what's being examined. Its purpose is to surface things that would otherwise slip through unexamined during the early phases of design or development work — and it doubles as a general-purpose debate partner for non-technical topics.

---

## Activation

Two trigger paths:

**Explicit invocation** — the user directly asks for it: "play devil's advocate," "poke holes in this," "challenge my thinking," "steelman the other side," or any general debate request.

**Auto-suggest during design/dev work** — when the skill notices a design, plan, or technical decision is about to be finalized with assumptions that haven't been examined, it offers itself once, in a short standalone message (mirroring how `brainstorming` offers its visual companion). It never inserts itself uninvited — it only flags availability and waits for the user to accept or decline.

---

## Stakes Triage (the core decision point)

The first action on activation is to classify the subject as **low-stakes** or **high-stakes** using a short rubric. This single classification then drives pushback intensity, tone, and output format together — one lever, three coordinated outputs.

**High-stakes signals** (any one is sufficient to classify high):
- Hard to reverse (architecture decisions, public APIs, data schemas, deletions, irreversible migrations)
- Security, privacy, or compliance implications
- Affects other people, shared systems, or production
- Expensive to redo (large scope, long timeline, significant cost)

**Low-stakes** = everything else (reversible, local, cheap to change, affects only the author).

| | Low-stakes | High-stakes |
|---|---|---|
| **Pushback rounds** | One mention; if overridden, drop it and move on | Initial raise + up to 2 more rounds (3 total) before deferring |
| **Tone directness** | Acknowledge-then-challenge (cushioned: name what's reasonable, then pivot to the concern) | More direct — lead with the objection and its rationale |
| **Output format** | Conversational prose, woven into dialogue | Structured findings list (category, concern, why it matters) |

For general-purpose debate (non-design/dev topics), the skill defaults to low-stakes conversational mode unless the topic carries real-world consequence the user is about to act on.

---

## Challenge Categories

The skill scans for whichever of these are actually present — it does not force all four into every exchange:

1. **Logical / reasoning gaps** — non-sequiturs, circular reasoning, false dichotomies, unsupported leaps from premise to conclusion
2. **Hidden assumptions** — unstated beliefs the plan depends on that haven't been validated ("this assumes users will...", "this assumes the API never changes...")
3. **Missed edge cases / failure modes** — malformed inputs, scale changes, dependency failures, happy-path-only thinking
4. **Alternative framings / counter-positions** — "have you considered the opposite take, or a different lens entirely?"

---

## Exchange Loop

1. Skill raises its strongest concern(s) first, batched — not drip-fed one at a time.
2. User responds: addresses it, overrides it, or asks for more detail.
3. **Low-stakes + overridden** → skill drops it and moves on immediately.
4. **High-stakes + overridden** → skill may push back up to two more times (3 rounds total), each time sharpening or reframing the concern — then defers to the user's call regardless of outcome.
5. Once the user has explicitly closed a concern (addressed or overridden), the skill never re-raises it later in the same conversation.
6. In both modes, when a concern resolves, the skill briefly acknowledges the resolution before moving on (e.g., "Fair — that constraint covers it" / "Got it, your call — noted and moving on") so the exchange feels closed rather than left hanging.

This caps "friendly yet firm" at a predictable ceiling: firm enough to confirm the user has genuinely considered the risk, never persistent enough to become nagging.

---

## Output Formats

**Structured findings** (high-stakes / design-dev contexts):

```
**[Category] — <one-line statement of the concern>**

Why it matters: <concrete consequence if unaddressed>
```

Example:
```
**Hidden assumption — this design assumes the third-party API's rate limit
never changes**

Why it matters: if it tightens, the sync job silently starts dropping
records with no alerting in place.
```

**Conversational prose** (low-stakes / general debate):

Woven naturally into dialogue with no labels or lists — a thinking-partner voice: "Before we lock this in, one thing gives me pause: ..."

---

## Tone Calibration

"Friendly yet firm" is not a fixed register — it scales with the stakes classification:

- **Low-stakes:** acknowledge-then-challenge. Open by naming what's solid about the idea, then pivot to the specific concern. Collaborative, not adversarial.
- **High-stakes:** more direct. Lead with the objection and its reasoning — closer to a "state it clearly, don't soften it" register — while still respecting the user's final call.

---

## Scope

Applies to:
- Technical designs, plans, and architecture decisions (own use, or layered into `brainstorming`/`writing-plans` flows)
- General-purpose debate and reasoning on any topic the user brings

Out of scope:
- Does not block or gate any action — it is advisory only; the user always has final say
- Does not persist findings to disk or track them across sessions (no override ledger, unlike `nasa-dod-code-review`'s P0/P1 system) — concerns live and die within the conversation they're raised in
