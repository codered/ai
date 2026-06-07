# Memory Index Schema

Defines the JSON structure for the three index files that make `memory/` lookups
fast. These are written and updated by the `memory` skill's sub-agent — both in
seed mode (building from scratch) and maintain mode (incremental updates) — and
read by any agent doing a quick "do we know about X?" check.

All JSON files use 2-space indentation and are kept small enough to load in full.

---

## `memory/index.json` — Top-level manifest

The entry point. An agent loads this first; its `tags` map answers "do we have
anything about X, and which tier(s) is it in?" without opening any entry file.

### Fields

- `updated_at` (string, ISO-8601 UTC timestamp) — when this file was last written
- `entry_count` (object) — `{ "short": <int>, "long": <int> }`, total entries per tier
- `tags` (object) — keyword → tier-pointer map. Each key is a lowercase, hyphenated
  tag. Each value is `{ "short": [<entry-id>, ...], "long": [<entry-id>, ...] }`.
  Either array may be empty but both keys must be present.

### Example

```json
{
  "updated_at": "2026-06-07T10:32:00Z",
  "entry_count": { "short": 18, "long": 42 },
  "tags": {
    "auth": {
      "short": ["auth-current-task"],
      "long": ["auth-architecture", "auth-history"]
    },
    "demo-pipeline": {
      "short": ["readme-pr3-status"],
      "long": ["vhs-setup", "demo-asset-conventions"]
    },
    "readme": {
      "short": ["readme-pr3-status"],
      "long": ["readme-restructure-rationale"]
    },
    "pr": {
      "short": ["readme-pr3-status"],
      "long": []
    }
  }
}
```

---

## `memory/short/_index.json` and `memory/long/_index.json` — Per-tier detail

One record per entry file in that tier. An agent opens this only after the
top-level `tags` map has pointed it at a specific tier.

### Fields (per entry record)

- `id` (string) — unique identifier within its tier, lowercase-hyphenated, matches the
  filename stem. The same conceptual fact split across both tiers (a short-tier pointer
  and its long-tier companion) uses two distinct `id`s, linked via `pointer`.
- `file` (string) — filename of the entry, relative to this index's folder (e.g. `"readme-pr3-status.md"`)
- `tags` (array of strings) — every tag this entry should be reachable under;
  each one MUST also appear in the top-level `index.json` `tags` map pointing to this `id`
- `summary` (string) — one sentence, scannable without opening the file
- `last_accessed` (string, `YYYY-MM-DD`) — date this entry was last read or referenced
- `access_count` (integer) — number of times this entry has been read or referenced;
  starts at `1` when an entry is created
- `pointer` (string, optional) — relative path from `memory/` to a companion entry in
  the *other* tier (e.g. `"long/readme-restructure-rationale.md"`). Omit this field
  entirely when no companion entry exists — do not write it as `null` or `""`. When
  both a short-tier pointer entry and its long-tier companion exist, the companion
  should carry a reciprocal `pointer` back, so the relationship can be navigated
  from either direction.

### Example

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

---

## Consistency rules (the sub-agent must keep these true on every write)

1. Every `id` referenced anywhere in `index.json`'s `tags` map must have a matching
   record in that tier's `_index.json` — and vice versa. No orphaned references.
2. Every tag listed on an entry record in a `_index.json` must appear in the
   top-level `tags` map with that entry's `id` listed under the matching tier.
3. `entry_count` in `index.json` must always equal the number of records in the
   corresponding `_index.json`.
4. When an entry is removed or re-filed into the other tier, remove its `id` from
   every tag list and record it no longer belongs to, in both the top-level and
   per-tier index files — don't leave stale references behind.
