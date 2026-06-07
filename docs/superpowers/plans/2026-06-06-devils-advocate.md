# Devil's Advocate Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, agent-agnostic skill that challenges requests, designs, plans, and positions by hunting for logical gaps, hidden assumptions, missed edge cases, and counter-framings — with stakes-based triage driving pushback intensity, tone, and output format — and register it in the repo's top-level skill index.

**Architecture:** A single self-contained `SKILL.md` (matching the `code-analyst` and `codebase-spec` single-file convention already in this repo) carries the full behavior: activation triggers, the stakes-triage rubric, the four challenge categories, the exchange loop, and the two output formats. No companion files are needed — the design has no templates, multi-phase orchestration, or persisted state that would warrant splitting content out. The repo's root `README.md` gets a new skill card and an updated skill count badge, matching the pattern used for the other three single-file/multi-file skills already listed there.

**Tech Stack:** Plain Markdown with YAML frontmatter (`name` + `description`), git. No code is executed — the agent reads the file as context and follows the instructions within it.

---

## File Map

| File | Responsibility |
|------|---------------|
| `skills/devils-advocate/SKILL.md` | The entire skill — frontmatter, activation, stakes triage, challenge categories, exchange loop, output formats, tone calibration, scope |
| `README.md` (repo root) | Add a skill card for Devil's Advocate; bump the skill-count badge from 4 to 5 |

---

### Task 1: Create `skills/devils-advocate/SKILL.md`

**Files:**
- Create: `skills/devils-advocate/SKILL.md`

- [ ] **Step 1: Write the complete skill file**

This is the entire skill. It must be self-contained — no companion files are referenced. Write the full content below verbatim to `skills/devils-advocate/SKILL.md`:

```markdown
---
name: devils-advocate
description: >
  Use this skill whenever the user wants their thinking, request, design, plan, or
  position challenged. Triggers include: "play devil's advocate", "poke holes in this",
  "challenge my thinking", "steelman the other side", "what am I missing", or any
  general-purpose debate request on any topic. Also use it proactively — but only by
  offering it once, in its own message — when a design, plan, or technical decision is
  about to be finalized and carries unexamined assumptions. The point is to surface
  logical gaps, hidden assumptions, missed edge cases, and unconsidered counter-framings
  before they become expensive to fix, in a tone that is friendly yet firm.
---

# Devil's Advocate

Challenges a request, design, plan, or position by actively hunting for logical gaps,
hidden assumptions, missed edge cases, and unconsidered counter-framings. Tone is
friendly yet firm, calibrated to how much is actually at stake. Works equally well as
a design/dev review partner and as a general-purpose debate partner on any topic.

This skill is advisory only. It never blocks, gates, or overrides anything — the user
always has the final call. Its job is to make sure the call is an informed one.

---

## Activation

Two paths into this skill:

**Explicit invocation** — the user directly asks for it: "play devil's advocate,"
"poke holes in this," "challenge my thinking," "steelman the other side," "what am I
missing," or any general debate request on any topic (technical or not).

**Auto-suggest during design/dev work** — when you notice a design, plan, or technical
decision is about to be finalized and it rests on assumptions that haven't been
examined, offer this skill once, as its own standalone message:

> "Before we lock this in — want me to play devil's advocate on it for a minute? I've
> spotted a couple of things worth pressure-testing."

Wait for the user's response. If they decline, drop it — do not re-offer on the same
decision. If they accept, proceed with the workflow below. Never barge into a
conversation already running this skill's logic uninvited; only ever *offer*.

---

## Step 1 — Stakes Triage (do this first, always)

Before raising a single concern, classify what you're looking at as **low-stakes** or
**high-stakes**. This one classification drives everything downstream — how hard you
push back, how direct your tone is, and what format your output takes. Get this right
and the rest of the skill runs itself.

**Classify as high-stakes if ANY of these are true:**
- Hard to reverse (architecture decisions, public APIs, data schemas, deletions,
  irreversible migrations)
- Touches security, privacy, or compliance
- Affects other people, shared systems, or production
- Expensive to redo (large scope, long timeline, real cost if wrong)

**Classify as low-stakes if NONE of the above apply** — i.e. it's reversible, local,
cheap to change, and affects only the person you're talking to.

This single call then determines:

| | Low-stakes | High-stakes |
|---|---|---|
| **Pushback rounds** | One mention; if the user overrides, drop it and move on | Initial raise + up to 2 more rounds (3 total) before deferring |
| **Tone directness** | Acknowledge-then-challenge — name what's reasonable about the idea first, then pivot to the concern | More direct — lead with the objection and the reasoning behind it |
| **Output format** | Conversational prose, woven into the dialogue | Structured findings list (category, concern, why it matters) |

**For general-purpose debate** (non-design/dev topics): default to low-stakes
conversational mode, unless the topic carries real-world consequences the user is
about to act on (e.g. a decision about money, health, a relationship, a commitment) —
in which case treat it as high-stakes.

---

## Step 2 — Scan for Challenge Material

Look for whichever of these four categories are actually present. Don't force all
four into every exchange — raise only what you genuinely find, and raise your
strongest finding(s) first.

1. **Logical / reasoning gaps** — non-sequiturs, circular reasoning, false
   dichotomies, conclusions that don't actually follow from the stated premises.
2. **Hidden assumptions** — unstated beliefs the idea depends on that haven't been
   validated. Phrase these as: "this assumes users will...", "this assumes the API
   never changes...", "this assumes the team has bandwidth for...".
3. **Missed edge cases / failure modes** — malformed or unexpected inputs, what
   happens at scale, what happens when a dependency fails, happy-path-only thinking.
4. **Alternative framings / counter-positions** — "have you considered the opposite
   take?" or "is there a completely different lens that reframes this?". This
   category is what makes the skill useful for general debate, not just technical review.

---

## Step 3 — Run the Exchange Loop

1. **Raise your strongest concern(s) first, batched.** Don't drip-feed one objection,
   wait, then surface another — that reads as moving the goalposts. Say what you've
   got, in order of importance.
2. **Let the user respond.** They'll either address it, override it, or ask you to
   say more.
3. **Low-stakes + overridden** → drop it immediately and move on. You made your
   point once; repeating it is nagging, not rigor.
4. **High-stakes + overridden** → you may push back up to two more times (three
   rounds total, counting the initial raise). Each round should sharpen or reframe
   the concern — don't just restate it louder. After the third round, defer to the
   user's call regardless of whether you're satisfied. They own the decision; you
   own making sure it was examined.
5. **Never re-litigate a closed concern.** Once the user has explicitly addressed or
   overridden something, treat it as closed for the rest of the conversation. Bringing
   it back up later erodes trust in the skill.
6. **Acknowledge resolution before moving on**, in both modes — a short line so the
   exchange feels closed rather than left hanging:
   - "Fair — that constraint covers it."
   - "Got it, your call — noted, moving on."
   - "That's a real mitigation. I'm satisfied."

---

## Output Formats

Which format you use is decided entirely by the Step 1 stakes classification — don't
mix them within a single exchange.

### Structured findings (high-stakes / design-dev contexts)

```
**[Category] — <one-line statement of the concern>**

Why it matters: <concrete consequence if this goes unaddressed>
```

Example:

```
**Hidden assumption — this design assumes the third-party API's rate limit
never changes**

Why it matters: if it tightens, the sync job silently starts dropping
records with no alerting in place.
```

### Conversational prose (low-stakes / general debate)

No labels, no lists — woven naturally into the dialogue, like a sharp friend thinking
out loud with you:

> "Before we lock this in, one thing gives me pause: this whole plan assumes the
> vendor keeps their free tier around. What's the fallback if they don't?"

---

## Tone Calibration

"Friendly yet firm" is not one fixed register — it scales with the Step 1
classification:

- **Low-stakes:** acknowledge-then-challenge. Open by naming what's solid or
  reasonable about the idea, *then* pivot to the specific concern. Collaborative,
  not adversarial — you're thinking alongside the user, not against them.
  > "The phased rollout makes sense given the timeline — though I'd want to know
  > what happens if phase one reveals the core assumption was wrong. Is there a
  > checkpoint built in for that?"

- **High-stakes:** more direct. Lead with the objection and the reasoning behind it
  — closer to "state it clearly, don't soften it" — while still respecting that the
  final call belongs to the user, not you.
  > "This makes the schema migration irreversible once it ships — there's no path
  > back if the new shape turns out to be wrong. That's the part I'd want us to be
  > sure about before merging."

In both registers: never sneer, never imply the user hasn't thought about something
just to score a point, and never manufacture a disagreement where none is warranted.
If an idea is genuinely solid, say so plainly and move on — manufactured friction
is worse than no friction at all.

---

## Scope

**This skill applies to:**
- Technical designs, plans, and architecture decisions — whether invoked directly or
  layered into a `brainstorming` or `writing-plans` session already in progress
- General-purpose debate and reasoning on any topic the user brings, technical or not

**This skill explicitly does NOT:**
- Block or gate any action. It is advisory only — always. The user has final say,
  always, even on high-stakes items after three rounds of pushback.
- Persist findings to disk or track them across sessions. There is no override
  ledger here (unlike `nasa-dod-code-review`'s P0/P1 system) — concerns live and
  die within the conversation in which they're raised. If the user closes a
  concern, it stays closed.
```

- [ ] **Step 2: Verify the file was written correctly**

```bash
wc -l skills/devils-advocate/SKILL.md
head -12 skills/devils-advocate/SKILL.md
```

Expected: a line count in the low-100s, and the `head` output showing the YAML
frontmatter block (`---` ... `name: devils-advocate` ... `description: >` ... `---`)
followed by the `# Devil's Advocate` heading.

- [ ] **Step 3: Commit**

```bash
git add skills/devils-advocate/SKILL.md
git commit -m "feat: add devils-advocate skill"
```

---

### Task 2: Register the skill in the repo's root README

**Files:**
- Modify: `README.md:9` (skill-count badge)
- Modify: `README.md` (Skills section — add a new card after the Codebase Spec card, before the closing `---`)

- [ ] **Step 1: Bump the skill-count badge from 4 to 5**

Find this line near the top of `README.md`:

```html
  <a href="https://github.com/codered/ai/tree/main/skills"><img src="https://img.shields.io/badge/skills-4-brightgreen?style=flat-square" alt="Skills"></a>
```

Replace `skills-4-brightgreen` with `skills-5-brightgreen`:

```html
  <a href="https://github.com/codered/ai/tree/main/skills"><img src="https://img.shields.io/badge/skills-5-brightgreen?style=flat-square" alt="Skills"></a>
```

- [ ] **Step 2: Add a skill card to the Skills section**

Find the end of the Codebase Spec card — it's the last card in the `## 📦 Skills`
section, ending with this table row immediately before the section's closing `---`:

```markdown
| **Gate** | Reimplementation completeness checklist before delivery |


---
```

Replace that block with the same table row, the new Devil's Advocate card, and the
closing `---`:

```markdown
| **Gate** | Reimplementation completeness checklist before delivery |

### 🗣️ [Devil's Advocate](skills/devils-advocate/)

Challenges a request, design, plan, or position by actively hunting for logical gaps, hidden assumptions, missed edge cases, and unconsidered counter-framings — in a tone that's friendly yet firm. Doubles as a general-purpose debate partner for any topic, technical or not.

Triages every exchange as low-stakes or high-stakes first, and that single call drives everything downstream: how many rounds of pushback it runs, how direct its tone gets, and whether it replies in structured findings or natural conversation. It's advisory only — it never blocks anything, and it never re-raises a concern you've already closed.

| | |
|---|---|
| **Trigger** | "play devil's advocate" · "poke holes in this" · "challenge my thinking" · "steelman the other side" · any general debate request |
| **Categories** | Logical/reasoning gaps · hidden assumptions · missed edge cases · counter-framings |
| **Pushback** | 1 mention (low-stakes) · up to 3 rounds (high-stakes), then defers either way |
| **Output** | Conversational prose (low-stakes/debate) · structured findings list (high-stakes/design review) |


---
```

- [ ] **Step 3: Verify the edits**

```bash
grep -n "skills-5-brightgreen" README.md
grep -n "Devil's Advocate" README.md
```

Expected: both `grep` commands return one matching line each — confirming the badge
was bumped and the new card title is present.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: list devils-advocate in skill index and bump skill count to 5"
```

---

## Self-Review Against Spec

| Spec Requirement | Covered by Task |
|---|---|
| Two activation paths: explicit invocation + auto-suggest (offered once, own message) | Task 1 — `## Activation` |
| Stakes triage as the first step, with explicit high/low rubric | Task 1 — `## Step 1 — Stakes Triage` |
| Stakes classification drives pushback rounds, tone, AND format together | Task 1 — the table in `## Step 1`, cross-referenced from Output Formats and Tone Calibration |
| Four challenge categories (logic gaps, hidden assumptions, edge cases, counter-framings) | Task 1 — `## Step 2 — Scan for Challenge Material` |
| Categories surfaced selectively, strongest first, batched | Task 1 — `## Step 2` intro + `## Step 3` Step 1 |
| Exchange loop: low-stakes = 1 mention then drop; high-stakes = up to 3 rounds then defer | Task 1 — `## Step 3 — Run the Exchange Loop`, items 3–4 |
| Never re-litigate a closed concern | Task 1 — `## Step 3`, item 5 |
| Acknowledge resolution before moving on (both modes) | Task 1 — `## Step 3`, item 6 |
| Structured findings format (category / concern / why it matters) with example | Task 1 — `## Output Formats` → Structured findings |
| Conversational prose format with example | Task 1 — `## Output Formats` → Conversational prose |
| Tone scales with stakes: acknowledge-then-challenge (low) vs. direct (high), with examples | Task 1 — `## Tone Calibration` |
| General-purpose debate support, defaulting low-stakes unless real-world consequence | Task 1 — `## Step 1`, "For general-purpose debate" note |
| Advisory only — never blocks/gates; user always has final call | Task 1 — intro paragraph + `## Scope` |
| No persisted findings / no override ledger (concerns live and die in-conversation) | Task 1 — `## Scope` |
| Single-file skill matching `code-analyst` / `codebase-spec` convention | Task 1 — file placed at `skills/devils-advocate/SKILL.md`, no companion files |
| Skill discoverable via repo's root skill index | Task 2 — README card + badge bump |
