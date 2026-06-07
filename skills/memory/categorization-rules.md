# Memory Categorization Rules

How the `memory` skill's sub-agent decides whether a piece of information belongs
in `short/` (active, frequently needed) or `long/` (full project detail) — and when
to move it from one to the other. Used during both seed mode (initial filing) and
maintain mode (re-filing existing entries).

Three signals are combined for every categorization decision. No single signal
decides placement on its own — weigh all three together.

---

## The three signals

### 1. Recency / active relevance

Is this tied to work that's currently in flight?

- **Leans short:** an open task, a bug currently being chased, a decision made in
  the last few sessions, a PR awaiting review, a question the user is actively
  working through right now.
- **Leans long:** settled, stable facts — architecture decisions that shipped
  months ago, conventions the team has followed for a while, project history,
  anything that isn't actively changing.

### 2. Frequency of access

How often has this been looked up across recent sessions?

- **Leans short**, regardless of how "settled" the fact is, when it keeps coming
  up — e.g. "this repo's tests require `VHS_NO_SANDBOX=true`" is a stable fact, but
  if it's been referenced repeatedly, cheap access matters more than its age.
- Use the `access_count` field (see `index-schema.md`) as the concrete signal: an
  entry with a rising `access_count` over multiple maintenance passes is a
  candidate for promotion to short, even if it would otherwise sit in long.

### 3. Scope / granularity

How much detail does this actually need to carry where it lives?

- **Short-tier entries are pointers and summaries** — sized for a quick scan.
  Example: `"PR #3 open, awaiting review — full history in long/readme-pr3-context.md"`.
- **Long-tier entries are the complete version** — full context, rationale, and
  history. Anything that would take more than a few sentences to convey belongs
  here, with a short pointer left behind in the other tier if it's still relevant
  to active work.

---

## Filing an entry (seed mode, or a brand-new fact in maintain mode)

1. Weigh all three signals together. There is no scoring formula — use judgment,
   but bias toward **short** when in doubt for anything tied to work that's
   plausibly still active, and toward **long** for anything that reads as settled
   history or background.
2. If the fact is detailed enough that a one-line summary would lose something
   important, write the full version to `long/`, and — only if the fact is *also*
   currently relevant to active work — add a short pointer entry in `short/` whose
   `pointer` field links to the long entry.
3. If the fact is small enough to stand on its own as a one-or-two-sentence note
   (e.g. "tests require `VHS_NO_SANDBOX=true`"), it can live in `short/` alone with
   no long-tier companion — there's nothing more to say about it.

## Re-filing an entry (maintain mode only)

During every maintenance pass, re-evaluate a bounded sample of existing entries
(see `maintain-prompt.md` for the sample size and selection rule) against the
three signals above:

- **Promote long → short** when `access_count` has risen noticeably since the
  last pass, or when the entry's subject has become part of currently active work.
  Write (or update) a short pointer entry; keep the long entry as the full version.
- **Demote short → long** when an entry's subject has gone quiet — no access in
  several passes, and the work it described reads as resolved or shelved. Move
  the full content to `long/` (creating an entry there if one doesn't already
  exist), note its resolution/closure in the text (e.g. "Resolved 2026-06-10 —
  merged in PR #4"), and remove the short-tier entry plus its tag references.
- Leave everything else exactly as it is — re-filing should touch the smallest
  possible set of entries and index records on each pass, so JSON diffs stay small
  and reviewable in git.
