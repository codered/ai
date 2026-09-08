# hashline Rules for Emitted Tasks

hashline is mandatory for editing existing files. Emitted task code must not use
`grep`, `sed`, string-replace edit tools, or `open(...).write()` — those bypass
the drift check that makes anchored editing worth having.

## Why anchors, not line numbers

Every line carries an `xxh32` hash. You target `line:hash`. If the file drifted
since the read, the patch is rejected instead of landing on the wrong line.
`Editor.locate()` is the replacement for search: it matches content in
hashline's own read output and hands back the anchor, so finding and
drift-checking are one act.

**Anchors are resolved at run time, never at plan time.** This is what lets
task 07's script — written before tasks 01–06 ran — still target the right line.

## The fallback ladder

| Situation | Response |
|---|---|
| Patch applies | `exit 0`, `backend: hashline` |
| hashline rejects on drift (`content changed since last read`) | `exit 3`, halt and replan. **Never fall back.** |
| Anchor content not present at all | `Drift` → `exit 3` |
| hashline binary missing, crashes, or returns non-JSON | AST/line fallback, `WARN: fallback backend used`, `backend: fallback` in the report |

**Drift halts; tool failure degrades.** Collapsing the two would let a genuine
conflict be silently overwritten by the fallback path.

## Exit contract

| Code | Meaning |
|---|---|
| `0` | Applied (or already applied) and all gates pass |
| `1` | Gate failed — the work is wrong |
| `3` | Drift — halt and replan |
| `4` | Manual task awaiting a human or agent edit |

## CLI facts (hashline 0.9.1)

- `hashline read --json <file>` → `{"hash", "path", "lines": [{"n", "hash", "content"}]}`
- `hashline patch --json [--dry-run] <file> <patch>` → `{"success": true, ...}` or
  `{"error": ...}` on stderr with stdout empty and exit status 1
- `hashline find-block --json <file> <line:hash>` → `{"block_lines": [...]}`
- On error, the JSON error object goes to **stderr** with stdout empty and exit status 1;
  on success the JSON is on stdout.
- `find-block` can report a line past the end of the file (e.g. `n=7`, empty content,
  for a 6-line file). `locate_block` discards only entries that are both beyond the
  file's known length AND empty; any remaining out-of-range entry raises `Drift`,
  because a file that grew under us is a stale snapshot, not something to guess about.
- Ops within one patch address **original** line numbers; do not re-number for
  earlier inserts or deletes in the same patch.
- Prefer `find-block` plus an explicit range `SWAP` over `SWAP.BLK`: `SWAP.BLK`
  replaces only the body around the anchor, which is not what "replace this
  function" means.
