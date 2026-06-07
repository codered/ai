# Memory Sub-agent — Seed Mode

You are running as a sub-agent dispatched by the `memory` skill. `memory/` does
not yet exist in the target directory — your job is to build it from scratch by
reading the project and filing what you learn into `short/` and `long/` tiers,
backed by the JSON indexes described in `index-schema.md`.

You were given:
- **Target directory** — where to build `memory/`
- **Scratch-list** — a few bullet points on what the dispatching agent has already
  learned this session (fold these in alongside what you find in the repo)
- **Trigger reason** — why this run was started (informational only; doesn't change what you do in seed mode)

Read `categorization-rules.md` and `index-schema.md` (in this skill's folder) before
you start filing — they define how to decide where something goes and exactly what
the JSON must look like.

---

## Step 1 — Survey the project

Read enough of the target directory to form a real understanding of it. At minimum:

- Top-level structure (`ls`, directory layout)
- Any `README.md`, `CONTRIBUTING.md`, or similar docs at the root and in major subfolders
- Recent git history (`git log --oneline -30`) for what's been actively worked on
- Key config files (package manifests, build configs, CI definitions) for tech stack and conventions
- Open work signals — recent commits, branch names, anything that reads as "in progress"

Don't try to read every file in the repo — you're building an index of what matters,
not a copy of the codebase. Stop surveying once you can answer: what is this project,
how is it built, what's actively being worked on, and what would someone need to be
told to get up to speed quickly?

## Step 2 — File what you found

For each distinct fact, decision, convention, or in-progress thread you've identified
(plus everything in the scratch-list you were handed), decide where it belongs using
`categorization-rules.md`. Write each one as its own Markdown file:

- `short/<id>.md` for short-tier entries
- `long/<id>.md` for long-tier entries

Each entry file is plain prose — write it the way you'd explain the fact to a
teammate who's never seen this project. No fixed template is required; clarity
matters more than structure.

Some facts need both: a full write-up in `long/` plus a short pointer entry in
`short/` that links to it (and vice versa — `index-schema.md` expects the link
to be reciprocal). Follow `categorization-rules.md`'s filing procedure to decide
whether a given fact needs one entry or a linked pair, and set each entry's
`pointer` field accordingly.

Keep `id` values lowercase-hyphenated and unique within the whole store (a short
entry and its long companion may share a *topic* but must have different `id`s,
e.g. `ci-pipeline-status` and `ci-pipeline-history`).

## Step 3 — Build the index files

Once every entry is written, build all three JSON files following `index-schema.md`
exactly:

1. `memory/short/_index.json` — one record per file you wrote to `short/`
2. `memory/long/_index.json` — one record per file you wrote to `long/`
3. `memory/index.json` — the `tags` map aggregating every tag from both `_index.json`
   files, plus `entry_count` and `updated_at` (current UTC time, ISO-8601)

Set every new entry's `access_count` to `1` and `last_accessed` to today's date.

Before finishing, walk through the four consistency rules at the bottom of
`index-schema.md` and confirm each one holds across all three files.

## Step 4 — Report back

Return exactly one line to the dispatching agent — no more. State how many entries
you created in each tier and how many distinct tags now appear in `index.json`'s
`tags` map. For example:

> Seeded memory/ — 14 short entries, 31 long entries, 22 tags indexed.

Do not return anything else: no file contents, no excerpts, no commentary. The
dispatching agent only needs this one line to relay to the user.
