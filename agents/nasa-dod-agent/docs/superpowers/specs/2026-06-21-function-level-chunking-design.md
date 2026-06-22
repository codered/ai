# Function-level chunking, retry caps, single-file targeting, and progress logging

**Status:** Approved, pending implementation plan
**Author:** Claude (with Harsh Singh)
**Date:** 2026-06-21

## Context

The agent currently reviews and fixes code at file granularity: each file is sent
to the LLM as a whole (one review call per file, one combined fix call per batch
of findings). Earlier work this session fixed several reliability bugs at that
granularity (a silent 2000-char truncation, cross-file batching that suppressed
findings, and added `review_samples` to fight LLM sampling noise).

The next step is to push that same "smaller context is more reliable" lesson
down one level: review and fix **one function at a time** instead of one file
at a time. This also surfaces the need for finer-grained retry/cost controls
(a per-file retry cap is too coarse once multiple unrelated functions in the
same file are tracked independently) and a way to target a single file
directly instead of always scanning a whole directory.

## Goals

- Review and fix code at function/method granularity, falling back gracefully
  to whole-file behavior wherever chunking isn't possible.
- Add a per-chunk fix-retry cap (already exists at file granularity from a
  prior fix; this generalizes the key to chunk identity).
- Add a global cap on total fix attempts across an entire review run,
  independent of the per-chunk cap and the outer iteration loop.
- Lower the default outer-loop iteration cap, since each iteration now does
  finer-grained (and therefore more numerous) work per file.
- Let the CLI target a single file, not just a directory.
- Log per-file and per-function progress lines to the console by default, so
  a user watching a long-running review can see what's happening.

## Non-goals

- Chunking nested/closures functions separately from their enclosing
  function — nested functions stay folded into the parent chunk.
- Perfect parsing of every language edge case (decorators, multi-line
  generics, lambdas-as-functions). Tree-sitter parse failures fall back to
  whole-file review; this is an accepted, logged degradation, not a bug to
  chase down further in this pass.
- Changing how patches are *applied* to disk (`FixParser.apply_patch` still
  operates on the full file's text via Search/Replace). Chunking only changes
  what context the LLM is shown when reviewing/drafting a fix.

## A. Chunking module & data model

New module `src/nasa_dod_agent/chunker.py`.

**Dependency:** `tree-sitter-languages` (bundles pre-built grammars for all 8
languages already in `review_code.EXTENSION_LANGUAGES` — python, javascript,
typescript, c, cpp, go, rust, java — so no per-language grammar build step is
needed).

```python
@dataclass
class CodeChunk:
    name: str          # function/method name, or "<file-level>"
    start_line: int     # 1-indexed, inclusive
    end_line: int        # 1-indexed, inclusive
    text: str            # exact source text of this chunk

def chunk_file(path: Path, language: str) -> list[CodeChunk]: ...
```

`chunk_file`:
1. Parses the file with the grammar for `language` (mapped from our internal
   language names — note `"c++"` → tree-sitter's `"cpp"`).
2. Walks the AST capturing **top-level** function/method definition nodes
   only (not nested closures/inner functions, which stay folded into their
   enclosing chunk). Per-language node types:
   - Python: `function_definition` (module-level and inside `class_definition` bodies)
   - JavaScript/TypeScript: `function_declaration`, `method_definition`
   - Go: `function_declaration`, `method_declaration`
   - C/C++: `function_definition`
   - Rust: `function_item`
   - Java: `method_declaration`, `constructor_declaration`
3. Everything **not** covered by a captured node's byte range (imports,
   top-level vars/consts, package/file doc comments, class field
   declarations) becomes one extra `CodeChunk(name="<file-level>", ...)`
   covering those gaps.
4. **Fallback:** if `language` has no grammar mapping, or parsing raises/
   produces no usable tree, return a single chunk spanning the whole file
   named `"<file-level>"` — i.e. today's whole-file behavior. This must never
   raise; chunking failures degrade silently to the old behavior.

**Model change** (`models.py`): `Finding.function_name: Optional[str] = None`.

This field is never asked of the LLM — after parsing a chunk's findings, the
calling code stamps `function_name = chunk.name` onto every `Finding`
returned for that chunk (ground truth from our parser, not LLM output), and
rewrites `line_number` from chunk-local to file-absolute by adding
`chunk.start_line - 1`.

## B. Node integration

**`review_code._run_review`** (shared by `review_code_node` and
`re_review_changed_node`):
- For each file: detect language (existing `EXTENSION_LANGUAGES` lookup),
  call `chunk_file`, then loop over chunks — one LLM call per chunk (same
  per-call-isolation principle as the existing per-file review, one level
  finer). Human prompt becomes
  `"Review the following function from {file}:\n{chunk.text}"` (or
  `"...the following file-level code..."` for the `<file-level>` chunk).
- `review_samples` (self-consistency sampling, already implemented) applies
  per chunk now instead of per file — same dedup-by-`(file_path, rule)`
  logic, just at finer grain. (Dedup key for *this* purpose intentionally
  stays file+rule, not file+function+rule, since samples are always of the
  *same* chunk and should collapse to one finding regardless.)
- Stamp `function_name`/offset `line_number` as described in section A before
  appending to the findings list.

**`generate_fixes_node`**:
- When building the fix prompt for a finding, re-chunk the file and look up
  the chunk whose `name == finding.function_name` (or the `<file-level>`
  chunk if `function_name` is `None`), and show only that chunk's text
  instead of the whole file via `_file_contents_context`.
- The patch's Search/Replace block is still applied against the real
  on-disk file via the existing `FixParser.apply_patch` (unchanged) — the
  "Search block must be unique in the file" rule still protects against
  ambiguous matches across functions.
- If a finding's `function_name` doesn't match any current chunk (e.g. a
  prior patch already renamed/removed the function), fall back to showing
  the whole file, same graceful-degradation pattern as chunking failures.

## C. Caps & config

Three independent knobs, each with a different scope:

| Field (in `RubricConfig` / `config.yaml`) | Scope | Old | New default |
|---|---|---|---|
| `max_fix_attempts_per_chunk` | One function/chunk's retry budget | `MAX_FIX_ATTEMPTS=2` (hardcoded) | `2`, now in config |
| `max_total_fix_attempts` | Sum of fix attempts across every chunk/file/iteration in the whole run | *(didn't exist)* | `20` |
| `max_iterations` | Outer review→fix→re-review loop | `10` | `5` |

- **Retry key**: `generate_fixes._finding_key` extends from
  `f"{file_path}::{rule}"` to `f"{file_path}::{function_name}::{rule}"`. Two
  distinct functions with the same rule violation in the same file are now
  tracked (and capped) independently — fixing a latent imprecision flagged
  during an earlier code review of the file-level version of this cap.
- **Global cap**: no new state field. `generate_fixes_node` computes
  `total_attempts_so_far = sum(state["fix_attempts"].values())` each call. If
  that's already `>= max_total_fix_attempts`, stop with a new
  `stop_reason = "max_total_fix_attempts"` (added to `cli.py`'s
  `_STOP_MESSAGES`). Otherwise, the batch of findings to attempt this round
  is trimmed so it can't push the running total past the cap mid-round.
- `config.py`'s `init_config` template gains both new fields under `limits:`,
  alongside `max_iterations`.

## D. CLI: target a single file

`review` (and `restore`/`status`) currently require `path` to be a directory
(`file_okay=False`). Change to accept either:

- A directory: unchanged behavior (full scan).
- A file: `.nasa-dod-agent/` (config, checkpoints, backups, state.json) lives
  in **the file's parent directory**. `GraphState` gains a new field,
  `target_file: Optional[str]`; when set, `_collect_files` skips
  globbing/excludes entirely and returns `[Path(target_file)]` directly.
  `target_path` itself remains a real directory throughout (the file's
  parent), so every existing piece of code that treats `target_path` as a
  directory for display/relative-path purposes (`_display_path`, backup
  dir placement, etc.) needs no changes.
- `cli.py` sets: `target_dir = project_path.parent if project_path.is_file()
  else project_path`; `target_file = str(project_path.absolute())` if a
  file, else `None`.

## E. Logging

Python's standard `logging` module (already used in `review_code.py` for
parse-failure warnings), not `click.echo` — keeps node code framework-
agnostic. `cli.py` configures it once at startup:

```python
logging.basicConfig(level=logging.INFO, format="%(message)s")
```

so INFO-level lines show up by default with no flags, undecorated (no
timestamps/logger names). Per-file summary + per-function detail:

```
Reviewing divide.go (1 function)
  └─ Divide
Fixing divide.go::Divide (P0: missing zero-divisor check)
Applying patch to divide.go
```

- `review_code_node`/`re_review_changed_node` log the per-file header line
  and one per-chunk line before each chunk's LLM call.
- `generate_fixes_node` logs one line per finding it's about to attempt,
  including severity and a short reason.
- `apply_fixes_node` logs which file it's writing a patch to.

## F. Testing & edge cases

- `chunker.py` gets its own test file: real tree-sitter parsing (not mocked)
  against small fixture snippets per language, asserting correct chunk
  names/line ranges, plus the fallback-to-whole-file behavior for
  unparseable/unsupported input.
- Existing `_run_review`/`generate_fixes`/`apply_fixes` tests are updated to
  account for chunk-level calls — most can mock `chunk_file` directly rather
  than relying on real parsing, the same way they already mock
  `_generate_patches`/`LLMClient`.
- Explicit edge cases to test:
  - A file with zero functions (e.g. pure constants) → just the
    `<file-level>` chunk.
  - A finding whose `function_name` no longer matches any chunk after a
    prior patch → falls back to whole-file context.
  - `max_total_fix_attempts` triggering mid-batch → trims the batch rather
    than refusing it outright.
  - `max_fix_attempts_per_chunk` exhausted for one function while a sibling
    function in the same file still has budget remaining → only the
    exhausted one is skipped.
  - CLI `review` invoked with a file path → `.nasa-dod-agent/` created next
    to the file, only that file reviewed.

## Open questions

None outstanding — all prior open questions were resolved during design
(language scope: all 8 via tree-sitter; chunking scope: review and fix;
logging detail: per-file + per-function; non-function code: `<file-level>`
chunk; overall cap scope: total fix attempts; `max_iterations` new default:
5; single-file config dir: file's parent directory).
