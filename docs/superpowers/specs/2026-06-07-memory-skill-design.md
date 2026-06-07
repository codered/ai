# Memory Skill — Design Spec
**Date:** 2026-06-07
**Status:** Approved

---

## Overview

A standalone, agent-agnostic skill that builds and maintains a persistent, file-based memory store for a project or directory. It splits what it learns into two tiers — **short-term** memory (information needed for ongoing work, or needed often) and **long-term** memory (the full detail on the project) — and backs both with JSON indexes so any agent can quickly answer "do we already know this, and if not, where should we look?" without reading every memory file in full.

Its purpose is to give agents continuity across sessions and across context resets: instead of re-deriving the same understanding of a codebase from scratch every time, an agent can consult `memory/` first, find a fast pointer to what it needs, and only read the full detail when the pointer says it's relevant.

---

## Activation

Two trigger paths:

**Explicit invocation, anytime** — the user directly asks for it: "build memory for this project," "update memory," "memory status," or similar. Runs immediately regardless of context level, and can target either the current project directory or an explicitly named one ("build memory for `~/projects/foo`").

**Self-estimate + periodic check-in** — the skill's `SKILL.md` instructs any agent following it to periodically gut-check its own context usage (a rough self-assessment: has it read a lot of large files, had a long back-and-forth, etc.), and when it estimates it has crossed roughly the **25%** mark, to **offer** to run the memory skill — capturing what's been learned in the session before that understanding risks being lost to summarization. This is an offer, not a silent auto-run; the user can decline and keep working. It mirrors how the `agent-team` skill keeps its shared memory current after every task action, except the trigger here is context pressure rather than task completion.

---

## Storage Layout

Defaults to a visible top-level folder in the target directory: **`memory/`**

```
memory/
├── index.json          ← top-level manifest: tag/keyword → entry pointers, tier (short/long)
├── short/
│   ├── _index.json     ← per-folder index: one record per short-memory entry
│   └── *.md            ← individual short-memory entry files
└── long/
    ├── _index.json     ← per-folder index: one record per long-memory entry
    └── *.md            ← individual long-memory entry files
```

- **Target directory resolution:** defaults to the project root where the skill is invoked, but honors an explicitly named directory.
- **Entry files** are Markdown — human-editable, diffable, easy to review in git.
- **Index files** are JSON — optimized for fast LLM parsing and lookup, not human readability. They are what make "do we have this?" a cheap question to answer.

---

## Categorization Rules (Short vs. Long)

Placement is decided by combining three signals — recency, frequency, and scope — rather than any single rule in isolation:

1. **Recency / active relevance** — information tied to work currently in flight (an open task, a bug being chased, a decision made this week) leans *short*. Settled, stable facts (architecture, conventions, project history) lean *long*.
2. **Frequency of access** — information the agent has needed repeatedly across sessions gets surfaced in *short* even when it's a stable fact, because it's looked up often enough that cheap access matters more than its "settledness" (e.g., "tests in this repo require `VHS_NO_SANDBOX=true`").
3. **Scope / granularity** — short-term entries are *pointers and summaries*, sized for a quick scan ("PR #3 open, awaiting review — full history in `long/readme-pr3-context.md`"). Long-term entries hold the *complete* version: full context, rationale, history.

**How this plays out:**
- A single piece of knowledge can exist in **both** tiers — a one-line pointer in `short/`, the full write-up in `long/`. The short entry's job is to say "this exists, here's the gist, here's where to find the rest."
- **Promotion and demotion are dynamic.** During a maintenance pass, the sub-agent re-evaluates a bounded sample of existing entries against these three signals: a long-dormant "active task" entry gets demoted to long-term (archived, with its resolution noted); a long-term fact that's being referenced often gets promoted into short-term (or gains a pointer there).
- This dynamic re-filing is what keeps short-term memory both *small* (fast to scan in full) and *relevant* (containing what's actually being used right now) — the two properties that make "is this here?" a fast question.

---

## Lookup / Index Design

Three JSON layers, unified into a single coherent scheme:

**`memory/index.json`** — the entry point, small enough to load in full on every memory check. Its `tags` map is the keyword manifest: an agent checking "do we know anything about X?" scans this one small object first and gets back candidate entry IDs plus which tier(s) hold them.

```json
{
  "updated_at": "2026-06-07T10:32:00Z",
  "entry_count": { "short": 18, "long": 42 },
  "tags": {
    "auth":          { "short": ["auth-current-task"], "long": ["auth-architecture", "auth-history"] },
    "demo-pipeline": { "short": [], "long": ["vhs-setup", "demo-asset-conventions"] },
    "readme":        { "short": ["readme-pr3-status"], "long": ["readme-restructure-rationale"] }
  }
}
```

**`memory/short/_index.json`** and **`memory/long/_index.json`** — per-folder detail, one record per entry file:

```json
{
  "entries": [
    {
      "id": "readme-pr3-status",
      "file": "readme-pr3-status.md",
      "tags": ["readme", "demo-pipeline", "pr"],
      "summary": "PR #3 (skill demo videos) opened, awaiting merge confirmation.",
      "last_accessed": "2026-06-06",
      "access_count": 4,
      "pointer": "long/readme-restructure-rationale.md"
    }
  ]
}
```

**Lookup flow:** check `index.json`'s tag map for the keyword → get candidate IDs and which tier(s) hold them → if found in `short`, the summary is usually enough on its own; if only in `long` (or the short entry's `pointer` says "see long for full context"), open that one specific `.md` file. The JSON always answers "do we have this, and where" without scanning Markdown content.

---

## Sub-agent Orchestration & Dispatch Contract

The skill **always** delegates the actual memory work to a sub-agent — this is the mechanism that keeps the main conversation's context from filling up with file reads and categorization reasoning.

**Main agent's job (cheap, stays in-context):**
1. Assemble a short scratch-list — a handful of bullet points on what's been learned, decided, or changed this session (file paths touched, decisions made, open threads). Not a transcript — just enough for the sub-agent to know what's new.
2. Note the trigger reason (`"user-requested"` / `"context-threshold"`).
3. Dispatch **one** sub-agent with: target directory, scratch-list, trigger reason. Wait for a one-line receipt.

**Sub-agent's job (does all the heavy lifting, self-detects mode):**
1. Check whether `memory/` already exists in the target directory.
2. **Absent → Seed mode:** read the repo (structure, docs, recent git history, key configs/READMEs), categorize findings per the three-signal rule, and write out `short/` and `long/` entries plus all three JSON index files from scratch.
3. **Present → Maintain mode:** load the existing (small) `index.json`, fold the scratch-list's new learnings into the right tier — creating new entries or appending to existing ones — re-evaluate a bounded sample of existing entries for promotion/demotion, and update only the affected index records. This keeps JSON diffs small and git-friendly; the whole store is never rewritten on every pass.
4. Return a **one-line status receipt**, e.g.:
   `"Indexed 3 new facts (readme, demo-pipeline), promoted 1 entry short→long, memory/ now has 19 short / 43 long entries."`

The sub-agent reads every file, writes every file, and does all categorization reasoning in its own isolated context. The main agent only ever sees the scratch-list it wrote itself and the one-line receipt that comes back — none of the heavy lifting ever touches the main conversation.

---

## Skill Package Structure

Following this repo's established convention — a `SKILL.md` with frontmatter as the entry point, companion files for anything that would bloat it:

```
skills/memory/
├── SKILL.md                  ← entry point: frontmatter, trigger phrases, the
│                                "offer at ~25% context" guidance, and the
│                                high-level flow (triage → dispatch → receipt)
├── seed-prompt.md            ← full instructions for the sub-agent's seed-mode pass
├── maintain-prompt.md        ← full instructions for the sub-agent's maintain-mode pass
├── categorization-rules.md   ← the three-signal rule plus promotion/demotion criteria, in detail
└── index-schema.md           ← JSON schema definitions for index.json / _index.json,
                                 with worked examples, so the sub-agent produces
                                 consistent JSON across both seed and maintain runs
```

**Draft frontmatter** (to be refined when the file is written):

```yaml
---
name: memory
description: >
  Use this skill when the user wants to build or update a persistent,
  fast-lookup memory store for a project or directory — categorized into
  short-term (active/frequent) and long-term (full detail) tiers with
  JSON indexes for quick relevance checks. Triggers include "build memory",
  "update memory", "memory status", and ongoing-context offers when the
  agent estimates it's nearing ~25% context usage...
---
```

**Why seed and maintain get separate companion files** rather than one combined prompt: each mode has a fundamentally different read pattern — a full repo scan versus targeted diff-folding — and combining them would force the sub-agent to filter out the irrelevant half on every run. `SKILL.md` simply tells the sub-agent which one to load, based on whether `memory/` already exists.

---

## Open Questions / Future Considerations

None outstanding — all core design questions (storage location, categorization rule, lookup format, trigger mechanism, and orchestration model) were resolved during brainstorming and are reflected above. Implementation specifics (exact prompt wording for `seed-prompt.md` / `maintain-prompt.md`, the precise JSON schema field list, and the bounded-sample size for re-evaluation during maintenance passes) are left to the implementation plan.
