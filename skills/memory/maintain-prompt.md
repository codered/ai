# Memory Sub-agent — Maintain Mode

You are running as a sub-agent dispatched by the `memory` skill. `memory/` already
exists in the target directory — your job is to fold in what's been learned since
the last run, and lightly re-file existing entries whose categorization has likely
changed, *without* rewriting the whole store.

You were given:
- **Target directory** — where the existing `memory/` lives
- **Scratch-list** — a few bullet points on what's been learned, decided, or
  changed this session
- **Trigger reason** — why this run was started (`"user-requested"` or `"context-threshold"`)

Read `categorization-rules.md` and `index-schema.md` (in this skill's folder) before
you start — they define how to decide where something goes, how to re-file existing
entries, and exactly what the JSON must look like.

---

## Step 1 — Load the existing index

Read `memory/index.json` in full — it's small by design. This tells you what topics
are already tracked and which tier each lives in. Do **not** read every entry file;
only open the specific `short/<id>.md` or `long/<id>.md` files that are directly
relevant to what you're about to do in Steps 2 and 3.

## Step 2 — Fold in the scratch-list

For each item in the scratch-list you were handed:

- **If it extends or updates something already tracked** (check the `tags` map for
  a matching topic), open that entry, fold the new information into its prose, and
  bump its `access_count` by 1 and `last_accessed` to today's date in the relevant
  `_index.json` record.
- **If it's genuinely new**, file it as a new entry following `categorization-rules.md`
  — same process as seed mode's Step 2 (write the `.md` file, decide the tier, add
  a pointer companion if warranted).

## Step 3 — Re-evaluate a bounded sample for re-filing

Pick **up to 5 entries** to re-evaluate against the three signals in
`categorization-rules.md` — prioritize:

1. Any short-tier entry whose `last_accessed` is noticeably stale compared to other
   active short-tier entries (a demotion candidate)
2. Any long-tier entry whose `access_count` is unusually high relative to similar
   long-tier entries, or which the scratch-list just touched (a promotion candidate)

For each one you decide to re-file, follow the "Re-filing an entry" steps in
`categorization-rules.md` — move the content, update both `_index.json` files and
the top-level `tags` map, and remove stale references. Leave the other entries in
your sample untouched if they still belong where they are; re-filing only entries
that have actually changed is what keeps this pass small.

## Step 4 — Update the index files

Apply only the changes from Steps 2 and 3 to the three JSON files — do not
regenerate them from scratch. Update `entry_count` and `updated_at` in
`memory/index.json` to reflect the final state. Then walk through the four
consistency rules at the bottom of `index-schema.md` and confirm each one still
holds.

## Step 5 — Report back

Return exactly one line to the dispatching agent — no more. State what changed:
how many entries were added, how many were re-filed (and in which direction), and
the resulting totals. For example:

> Indexed 3 new facts (readme, demo-pipeline), promoted 1 entry long→short, memory/ now has 19 short / 43 long entries.

Do not return anything else: no file contents, no excerpts, no commentary. The
dispatching agent only needs this one line to relay to the user.
