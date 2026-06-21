# Function-Level Chunking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the review/fix agent from file-granularity to function/method-granularity, with finer-grained retry caps, a single-file CLI target, and console progress logging.

**Architecture:** A new `chunker.py` module splits a source file into per-function `CodeChunk`s (via `tree-sitter`) plus one `<file-level>` chunk for everything outside a function, falling back to a single whole-file chunk on any unsupported language or parse failure. `review_code._run_review` and `generate_fixes_node` are rewired to operate per-chunk instead of per-file. Three independent caps (`max_fix_attempts_per_chunk`, `max_total_fix_attempts`, `max_iterations`) bound total work. `cli.py` accepts a file path in addition to a directory, and configures `logging` so progress is visible by default.

**Tech Stack:** Python 3.11+, `tree-sitter` 0.21.x + `tree-sitter-languages` 1.10.x (pre-built grammars for all 8 supported languages), existing `pydantic`/`click`/`langgraph` stack.

## Global Constraints

- `tree-sitter-languages` 1.10.x only works with `tree-sitter<0.22` (newer `tree-sitter` changed the `Language` constructor signature and breaks `get_parser`/`get_language`) — pin both exactly as specified in Task 1.
- Spec reference: `docs/superpowers/specs/2026-06-21-function-level-chunking-design.md`. Every task below implements one or more of its sections (A–F).
- Per the spec's non-goals: nested/closure functions are never split into their own chunks; patch application (`FixParser.apply_patch`) is unchanged — chunking only changes what context the LLM sees.
- All new `RubricConfig` fields must have defaults that don't change behavior for existing configs that don't set them (additive, backward compatible).

---

### Task 1: Add tree-sitter dependency and the chunker module

**Files:**
- Modify: `pyproject.toml`
- Create: `src/nasa_dod_agent/chunker.py`
- Test: `tests/test_chunker.py`

**Interfaces:**
- Produces: `nasa_dod_agent.chunker.CodeChunk` (dataclass: `name: str`, `start_line: int`, `end_line: int`, `text: str`), `nasa_dod_agent.chunker.chunk_file(path: Path, language: str) -> list[CodeChunk]`, `nasa_dod_agent.chunker.FILE_LEVEL` (the string constant `"<file-level>"`).

- [ ] **Step 1: Add the dependency**

Edit `pyproject.toml`'s `dependencies` list (currently lines 8–15):

```toml
dependencies = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "pydantic>=2.0",
    "click>=8.0",
    "pyyaml>=6.0",
    "tree-sitter>=0.21,<0.22",
    "tree-sitter-languages>=1.10,<2.0",
]
```

Run: `uv sync`
Expected: installs `tree-sitter` and `tree-sitter-languages` with no errors.

- [ ] **Step 2: Write the failing tests**

Create `tests/test_chunker.py`:

```python
from unittest.mock import patch

import pytest

from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file


def test_chunk_go_file_splits_functions_and_file_level(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "import \"fmt\"\n"
        "\n"
        "// Divide returns a / b.\n"
        "func Divide(a, b int) int {\n"
        "\treturn a / b\n"
        "}\n"
        "\n"
        "func main() {\n"
        "\tfmt.Println(Divide(4, 2))\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")

    names = [c.name for c in chunks]
    assert names == ["Divide", "main", FILE_LEVEL]


def test_chunk_includes_leading_doc_comment_in_function_chunk(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "// Divide returns a / b.\n"
        "func Divide(a, b int) int {\n"
        "\treturn a / b\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")
    divide_chunk = next(c for c in chunks if c.name == "Divide")

    assert "// Divide returns a / b." in divide_chunk.text
    assert divide_chunk.start_line == 3


def test_chunk_file_level_excludes_function_bodies(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "const MaxRetries = 3\n"
        "\n"
        "func Foo() {\n"
        "\tx := 1\n"
        "\t_ = x\n"
        "}\n"
    )

    chunks = chunk_file(target, "go")
    file_level = next(c for c in chunks if c.name == FILE_LEVEL)

    assert "const MaxRetries" in file_level.text
    assert "x := 1" not in file_level.text


def test_chunk_python_methods_and_module_functions(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text(
        "import os\n"
        "\n"
        "class Foo:\n"
        "    def bar(self):\n"
        "        pass\n"
        "\n"
        "def baz():\n"
        "    pass\n"
    )

    chunks = chunk_file(target, "python")

    names = sorted(c.name for c in chunks)
    assert names == sorted(["bar", "baz", FILE_LEVEL])


def test_chunk_does_not_descend_into_nested_functions(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text(
        "def outer():\n"
        "    def inner():\n"
        "        pass\n"
        "    return inner\n"
    )

    chunks = chunk_file(target, "python")

    names = [c.name for c in chunks]
    assert names == ["outer"]
    assert "def inner" in chunks[0].text


def test_chunk_c_function_name_extracted_from_declarator(tmp_path):
    target = tmp_path / "sample.c"
    target.write_text("int add(int a, int b) { return a + b; }\n")

    chunks = chunk_file(target, "c")

    assert [c.name for c in chunks] == ["add"]


def test_chunk_unsupported_language_returns_whole_file(tmp_path):
    target = tmp_path / "sample.rb"
    target.write_text("def foo\n  1\nend\n")

    chunks = chunk_file(target, "ruby")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL
    assert chunks[0].text == target.read_text()


def test_chunk_file_with_no_functions_returns_whole_file(tmp_path):
    target = tmp_path / "consts.go"
    target.write_text("package sample\n\nconst MaxRetries = 3\n")

    chunks = chunk_file(target, "go")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL


def test_chunk_parser_failure_falls_back_to_whole_file(tmp_path):
    target = tmp_path / "sample.go"
    target.write_text("package sample\n\nfunc Foo() {}\n")

    with patch("nasa_dod_agent.chunker.get_parser", side_effect=RuntimeError("boom")):
        chunks = chunk_file(target, "go")

    assert len(chunks) == 1
    assert chunks[0].name == FILE_LEVEL
    assert chunks[0].text == target.read_text()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_chunker.py -v`
Expected: `ModuleNotFoundError: No module named 'nasa_dod_agent.chunker'` (collection error) for every test.

- [ ] **Step 4: Implement the chunker module**

Create `src/nasa_dod_agent/chunker.py`:

```python
"""Split a source file into per-function/method chunks via tree-sitter.

Falls back to a single whole-file chunk whenever the language isn't
supported or parsing doesn't yield anything useful — chunking failures
must never block a review, they just lose the finer granularity.
"""

import warnings
from dataclasses import dataclass
from pathlib import Path

from tree_sitter_languages import get_parser

# tree-sitter-languages 1.10.x targets an older tree-sitter Language API;
# the pin in pyproject.toml keeps it working, but the call still emits a
# harmless FutureWarning on every parser fetch.
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")

FILE_LEVEL = "<file-level>"

# Top-level function/method definition node types per language. Anything
# of these types is captured as its own chunk; their children are never
# descended into, so nested/closure functions stay folded into the
# enclosing chunk rather than becoming chunks of their own.
_FUNCTION_NODE_TYPES: dict[str, frozenset[str]] = {
    "python": frozenset({"function_definition"}),
    "javascript": frozenset({"function_declaration", "method_definition"}),
    "typescript": frozenset({"function_declaration", "method_definition"}),
    "go": frozenset({"function_declaration", "method_declaration"}),
    "c": frozenset({"function_definition"}),
    "c++": frozenset({"function_definition"}),
    "rust": frozenset({"function_item"}),
    "java": frozenset({"method_declaration", "constructor_declaration"}),
}

# Our internal language names (review_code.EXTENSION_LANGUAGES values) to
# the grammar name tree-sitter-languages expects.
_TS_LANGUAGE_NAMES: dict[str, str] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "go": "go",
    "c": "c",
    "c++": "cpp",
    "rust": "rust",
    "java": "java",
}

_COMMENT_NODE_TYPES = frozenset({"comment", "line_comment", "block_comment"})

# Declarator wrapper node types that hold a name directly (vs. another
# nested declarator) once unwrapped — C/C++ nest a function's name inside
# a chain of pointer/array/qualifier declarator nodes instead of exposing
# it as a "name" field on the function_definition node itself.
_DECLARATOR_NAME_TYPES = frozenset(
    {"identifier", "field_identifier", "qualified_identifier", "destructor_name"}
)


@dataclass
class CodeChunk:
    name: str
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    text: str


def chunk_file(path: Path, language: str) -> list[CodeChunk]:
    """Split ``path`` into one chunk per top-level function/method, plus
    one ``FILE_LEVEL`` chunk for everything else (imports, top-level
    vars/consts, doc comments, class fields). Falls back to a single
    whole-file chunk if ``language`` isn't supported or nothing parses.
    """
    source = path.read_text()
    ts_language = _TS_LANGUAGE_NAMES.get(language)
    target_types = _FUNCTION_NODE_TYPES.get(language)

    if ts_language is None or target_types is None:
        return [_whole_file_chunk(source)]

    try:
        parser = get_parser(ts_language)
        tree = parser.parse(source.encode())
    except Exception:
        return [_whole_file_chunk(source)]

    function_nodes: list = []
    _collect_function_nodes(tree.root_node, target_types, function_nodes)

    if not function_nodes:
        return [_whole_file_chunk(source)]

    function_nodes.sort(key=lambda n: n.start_byte)
    source_bytes = source.encode()

    chunks: list[CodeChunk] = []
    covered: list[tuple[int, int]] = []
    for node in function_nodes:
        start_node = _with_leading_comments(node)
        name = _function_name(node) or f"<anonymous_L{node.start_point[0] + 1}>"
        chunks.append(
            CodeChunk(
                name=name,
                start_line=start_node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                text=source_bytes[start_node.start_byte : node.end_byte].decode(),
            )
        )
        covered.append((start_node.start_byte, node.end_byte))

    gap_text = _gaps_text(source_bytes, covered)
    if gap_text.strip():
        chunks.append(
            CodeChunk(
                name=FILE_LEVEL,
                start_line=1,
                end_line=len(source.splitlines()) or 1,
                text=gap_text,
            )
        )

    return chunks


def _whole_file_chunk(source: str) -> CodeChunk:
    return CodeChunk(
        name=FILE_LEVEL, start_line=1, end_line=len(source.splitlines()) or 1, text=source
    )


def _collect_function_nodes(node, target_types: frozenset[str], out: list) -> None:
    if node.type in target_types:
        out.append(node)
        return  # don't descend — nested/closure functions stay folded in
    for child in node.children:
        _collect_function_nodes(child, target_types, out)


def _function_name(node) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode()
    # C/C++ function_definition nests the name inside a chain of
    # pointer/array/qualifier declarator wrappers instead of a "name"
    # field on the function node itself.
    declarator = node.child_by_field_name("declarator")
    while declarator is not None and declarator.type not in _DECLARATOR_NAME_TYPES:
        declarator = declarator.child_by_field_name("declarator")
    return declarator.text.decode() if declarator else None


def _with_leading_comments(node):
    """Walk backward over immediately-adjacent comment siblings (no blank
    line in between) so a function's doc comment travels with its own
    chunk instead of being orphaned in the file-level chunk."""
    start_node = node
    sibling = node.prev_sibling
    while sibling is not None and sibling.type in _COMMENT_NODE_TYPES:
        if start_node.start_point[0] - sibling.end_point[0] > 1:
            break
        start_node = sibling
        sibling = sibling.prev_sibling
    return start_node


def _gaps_text(source_bytes: bytes, covered: list[tuple[int, int]]) -> str:
    """Concatenate every byte range NOT covered by a function chunk."""
    pieces = []
    cursor = 0
    for start, end in covered:
        if start > cursor:
            pieces.append(source_bytes[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(source_bytes):
        pieces.append(source_bytes[cursor:])
    return b"".join(pieces).decode()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_chunker.py -v`
Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/nasa_dod_agent/chunker.py tests/test_chunker.py
git commit -m "feat(nasa-dod-agent): add tree-sitter-backed function chunker"
```

---

### Task 2: New config fields — `Finding.function_name`, retry caps, lower `max_iterations`

**Files:**
- Modify: `src/nasa_dod_agent/models.py`
- Modify: `src/nasa_dod_agent/config.py`
- Test: `tests/test_models.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing new from Task 1.
- Produces: `Finding.function_name: Optional[str]` (default `None`); `RubricConfig.max_fix_attempts_per_chunk: int` (default `2`); `RubricConfig.max_total_fix_attempts: int` (default `20`); `RubricConfig.max_iterations` default changed from `10` to `5`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_models.py` (after the existing `test_rubric_config_review_samples_default` test):

```python
def test_finding_function_name_defaults_to_none():
    f = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D", why_fix="W",
    )
    assert f.function_name is None


def test_rubric_config_max_iterations_lowered_to_five():
    """max_iterations dropped from 10 to 5 — with per-chunk reviewing now
    doing finer-grained work per iteration, fewer outer-loop iterations
    should be needed to converge."""
    assert RubricConfig().max_iterations == 5


def test_rubric_config_max_fix_attempts_per_chunk_default():
    assert RubricConfig().max_fix_attempts_per_chunk == 2


def test_rubric_config_max_total_fix_attempts_default():
    assert RubricConfig().max_total_fix_attempts == 20
```

Add to `tests/test_config.py` (after `test_load_review_samples_from_llm_section`):

```python
def test_init_config_writes_new_limit_fields(temp_project):
    ConfigLoader.init_config(temp_project)
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    content = config_path.read_text()
    assert "max_iterations: 5" in content
    assert "max_fix_attempts_per_chunk: 2" in content
    assert "max_total_fix_attempts: 20" in content

def test_load_new_limit_fields_from_yaml(temp_project):
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "limits:\n"
        "  max_fix_attempts_per_chunk: 4\n"
        "  max_total_fix_attempts: 50\n"
    )
    loaded = ConfigLoader.load(temp_project)
    assert loaded.max_fix_attempts_per_chunk == 4
    assert loaded.max_total_fix_attempts == 50
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py tests/test_config.py -v`
Expected: `test_finding_function_name_defaults_to_none` fails with `AttributeError` (no such field); `test_rubric_config_max_iterations_lowered_to_five` fails with `assert 10 == 5`; the two `max_fix_attempts_per_chunk`/`max_total_fix_attempts` default tests fail with `AttributeError`; both new config tests fail (assertion on text not present / `AttributeError`).

- [ ] **Step 3: Implement the model changes**

In `src/nasa_dod_agent/models.py`, update the `Finding` class (currently lines 27–35):

```python
class Finding(BaseModel):
    """A single NASA/DOD review finding."""
    severity: Severity
    file_path: str
    line_number: Optional[int] = None
    rule: str = Field(..., description="Standard name + rule number")
    description: str
    why_fix: str = Field(..., description="Why this must be fixed")
    fix_options: List[FixOption] = Field(default_factory=list)
    function_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the function/method this finding belongs to, stamped "
            "by the reviewer from the chunk it came from — None means it "
            "came from the file-level chunk (imports, top-level decls)."
        ),
    )
```

And update `RubricConfig` (currently lines 46–66):

```python
class RubricConfig(BaseModel):
    """User-configurable rubric thresholds."""
    max_p0: int = Field(default=0, ge=0)
    max_p1: int = Field(default=2, ge=0)
    max_p2: int = Field(default=5, ge=0)
    max_p3: int = Field(default=999, ge=0)
    fix_threshold: int = Field(
        default=1, ge=0, le=3,
        description="0=fix none, 1=fix P0+P1, 2=fix P0+P1+P2, 3=fix all"
    )
    max_iterations: int = Field(default=5, ge=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    review_samples: int = Field(
        default=1, ge=1,
        description=(
            "Times to review each file; findings are unioned across "
            "samples (deduped by file+rule) to catch issues a noisy model "
            "only reports on some of its attempts."
        ),
    )
    max_fix_attempts_per_chunk: int = Field(
        default=2, ge=1,
        description=(
            "One function/chunk's own retry budget — once a specific "
            "finding has been attempted this many times without "
            "resolving, stop retrying it (but keep fixing everything "
            "else)."
        ),
    )
    max_total_fix_attempts: int = Field(
        default=20, ge=1,
        description=(
            "Ceiling on the sum of fix attempts across every chunk/file/"
            "iteration in the whole run — stops the run even if no single "
            "chunk has hit its own per-chunk cap, to bound total work on "
            "repos with many small findings."
        ),
    )
```

- [ ] **Step 4: Implement the config template changes**

In `src/nasa_dod_agent/config.py`, update `init_config`'s `config_path.write_text(...)` call (currently lines 57–83) — only the `limits:` section changes:

```python
        config_path.write_text(
            "rubric:\n"
            f"  max_p0: {default.max_p0}\n"
            f"  max_p1: {default.max_p1}\n"
            f"  max_p2: {default.max_p2}\n"
            f"  max_p3: {default.max_p3}\n"
            "  # 0 = fix nothing, 1 = fix P0+P1, 2 = fix P0+P1+P2, 3 = fix everything\n"
            f"  fix_threshold: {default.fix_threshold}\n"
            "\n"
            "limits:\n"
            f"  max_iterations: {default.max_iterations}\n"
            "  # One function/chunk's own retry budget before giving up on it.\n"
            f"  max_fix_attempts_per_chunk: {default.max_fix_attempts_per_chunk}\n"
            "  # Total fix attempts across the whole run, summed over every\n"
            "  # chunk/file/iteration.\n"
            f"  max_total_fix_attempts: {default.max_total_fix_attempts}\n"
            "\n"
            "llm:\n"
            f"  temperature: {default.temperature}\n"
            f"  max_tokens: {default.max_tokens}\n"
            "  # Times to review each file; findings are unioned across "
            "samples to catch\n"
            "  # issues a noisy/local model only reports on some attempts. "
            "1 = no retry.\n"
            f"  review_samples: {default.review_samples}\n"
            "\n"
            "exclude:\n"
            "  - \"**/node_modules/**\"\n"
            "  - \"**/.git/**\"\n"
            "  - \"**/venv/**\"\n"
            "  - \"**/__pycache__/**\"\n"
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py tests/test_config.py -v`
Expected: all PASS.

- [ ] **Step 6: Run the full suite to check for regressions from the lowered `max_iterations` default**

Run: `uv run pytest -v`
Expected: all PASS — no existing test asserts the old `max_iterations == 10` default (they all either pass it explicitly or use `RubricConfig()` without checking that field).

- [ ] **Step 7: Commit**

```bash
git add src/nasa_dod_agent/models.py src/nasa_dod_agent/config.py tests/test_models.py tests/test_config.py
git commit -m "feat(nasa-dod-agent): add function_name and fix-attempt cap config fields"
```

---

### Task 3: Wire chunking into `review_code`, add `target_file` state, add progress logging

**Files:**
- Modify: `src/nasa_dod_agent/state.py`
- Modify: `src/nasa_dod_agent/nodes/review_code.py`
- Test: `tests/test_review_code.py`

**Interfaces:**
- Consumes: `nasa_dod_agent.chunker.CodeChunk`, `chunk_file`, `FILE_LEVEL` (Task 1); `Finding.function_name` (Task 2).
- Produces: `GraphState.target_file: Optional[str]`; `_collect_files(target_path, mode, last_modified, target_file=None)` (new keyword arg); `_run_review` now logs progress and stamps `function_name`/offsets `line_number` on every returned `Finding`.

- [ ] **Step 1: Add `target_file` to `GraphState`**

In `src/nasa_dod_agent/state.py`, add a field after `last_modified_files` (currently line 16):

```python
    findings: List[Finding]
    files_reviewed: List[str]
    last_modified_files: List[str]
    # Set when the CLI was pointed at a single file rather than a
    # directory — when present, review_code._collect_files returns just
    # this file instead of globbing target_path.
    target_file: Optional[str]
    # Count of fix attempts per finding, keyed by "{file_path}::{rule}".
```

(Leave the rest of the file, including the `fix_attempts` comment immediately below, unchanged — just insert the `target_file` field and its comment between `last_modified_files` and the existing `fix_attempts` line.)

- [ ] **Step 2: Write the failing tests**

Add to `tests/test_review_code.py` (the `Path`, `MagicMock`, `patch` imports already present cover what's needed; add `from nasa_dod_agent.chunker import FILE_LEVEL` and `from nasa_dod_agent.nodes.review_code import _collect_files` to the existing import line):

```python
from nasa_dod_agent.chunker import FILE_LEVEL
from nasa_dod_agent.nodes.review_code import _collect_files, _detect_languages, _run_review, review_code_node
```

(this replaces the existing `from nasa_dod_agent.nodes.review_code import ...` import line)

Then append these tests:

```python
def test_collect_files_returns_only_target_file_when_set(temp_project):
    (temp_project / "a.go").write_text("package a\n")
    (temp_project / "b.go").write_text("package b\n")
    target_file = str(temp_project / "a.go")

    files = _collect_files(str(temp_project), "full", [], target_file=target_file)

    assert files == [Path(target_file)]


def test_collect_files_globs_normally_when_no_target_file(temp_project):
    (temp_project / "a.go").write_text("package a\n")

    files = _collect_files(str(temp_project), "full", [], target_file=None)

    assert files == [temp_project / "a.go"]


def test_run_review_stamps_function_name_and_offsets_line_number(temp_project):
    target = temp_project / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "func Foo() {\n"
        "\tx := 1\n"
        "}\n"
    )

    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = (
        '[{"severity": "P2", "file_path": "sample.go", "rule": "R", '
        '"description": "D", "why_fix": "W", "line_number": 2}]'
    )

    findings = _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert len(findings) == 1
    assert findings[0].function_name == "Foo"
    assert findings[0].line_number == 4


def test_run_review_logs_file_and_function_progress(temp_project, caplog):
    target = temp_project / "sample.go"
    target.write_text("package sample\n\nfunc Foo() {}\n")

    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = "[]"

    caplog.set_level("INFO")
    _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert "Reviewing sample.go (1 function)" in caplog.text
    assert "Foo" in caplog.text
```

(`StandardsLoader` is already imported in this file from the earlier session's work.)

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_review_code.py -v -k "target_file or stamps_function_name or logs_file_and_function"`
Expected: the `_collect_files` tests fail with `TypeError: _collect_files() got an unexpected keyword argument 'target_file'`; `test_run_review_stamps_function_name_and_offsets_line_number` fails on `assert findings[0].function_name == "Foo"` (currently `None`); `test_run_review_logs_file_and_function_progress` fails because no log records are emitted.

- [ ] **Step 4: Implement `_collect_files` with `target_file`**

In `src/nasa_dod_agent/nodes/review_code.py`, replace `_collect_files` (currently lines 200–211):

```python
def _collect_files(
    target_path: str, mode: str, last_modified: List[str], target_file: str | None = None
) -> List[Path]:
    """Collect files to review based on mode.

    ``target_file``, when set, means the CLI was pointed at a single file
    rather than a directory — return just that file, ignoring mode and
    the exclude globs entirely.
    """
    if target_file:
        return [Path(target_file)]

    target = Path(target_path)
    if mode == "incremental" and last_modified:
        return [Path(f) for f in last_modified if Path(f).exists()]

    files = []
    for ext in EXTENSION_LANGUAGES:
        files.extend(target.rglob(f"*{ext}"))
    # Exclude common non-source
    exclude = {"node_modules", ".git", "venv", "__pycache__", ".nasa-dod-agent"}
    return [f for f in files if not any(part in exclude for part in f.parts)]
```

- [ ] **Step 5: Implement chunked `_run_review` with logging**

In `src/nasa_dod_agent/nodes/review_code.py`:

1. Add to the imports at the top of the file (after the existing `import json` / `import re` lines):

```python
import logging
```

And add this import alongside the other `nasa_dod_agent` imports:

```python
from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file
```

2. Add a module-level logger right after the imports, before `_extract_findings`:

```python
logger = logging.getLogger(__name__)
```

3. Replace `_run_review` (currently lines 254–295) with:

```python
def _run_review(
    files: List[Path],
    llm_client: LLMClient,
    loader: StandardsLoader,
    base_path: Path,
    samples: int = 1,
) -> List[Finding]:
    """Call LLM to review the collected files, one function/chunk per call.

    Each file is split into chunks (one per top-level function/method,
    plus a file-level chunk for everything else) via ``chunk_file`` — a
    real run showed that batching even two small, unrelated files into
    one prompt made the model report zero findings, even though it
    reliably caught the exact same issue when shown the offending content
    alone. Reviewing one chunk per call costs more calls but avoids that
    dilution.

    ``samples`` reviews each chunk that many times and unions the results
    (deduped per chunk) — a real run showed the same content, same
    prompt, returning findings on one call and none on the next at
    temperature 0.2, so a single sample isn't reliable evidence of a
    clean chunk on a noisy model.
    """
    findings: List[Finding] = []
    for f in files:
        display_path = _display_path(f, base_path)
        language = EXTENSION_LANGUAGES.get(f.suffix, "")
        chunks = chunk_file(f, language)

        function_count = sum(1 for c in chunks if c.name != FILE_LEVEL)
        noun = "function" if function_count == 1 else "functions"
        logger.info("Reviewing %s (%d %s)", display_path, function_count, noun)

        for chunk in chunks:
            logger.info("  └─ %s", chunk.name)
            label = "file-level code" if chunk.name == FILE_LEVEL else f"function {chunk.name}"
            system_prompt = loader.build_system_prompt(languages=_detect_languages([f]))
            human_prompt = f"Review the following {label} from {display_path}:\n\n{chunk.text}"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            chunk_findings: List[Finding] = []
            for _ in range(samples):
                raw = llm_client.get_llm().invoke(messages)
                chunk_findings.extend(_parse_llm_response(str(raw.content)))

            for finding in chunk_findings:
                finding.function_name = None if chunk.name == FILE_LEVEL else chunk.name
                if finding.line_number is not None:
                    finding.line_number += chunk.start_line - 1

            findings.extend(_dedupe_findings(chunk_findings))

    return findings
```

(This replaces the old whole-file loop body and removes the final module-level `_dedupe_findings(findings)` call — dedup now happens per chunk, right after that chunk's samples are collected, because two *different* chunks can legitimately produce findings sharing the same `rule` string and must not be collapsed together.)

4. Update `review_code_node` (currently lines 300–321) to pass `target_file` through:

```python
def review_code_node(state: GraphState) -> dict:
    """Review code and return findings."""
    files = _collect_files(
        state["target_path"],
        state["review_mode"],
        state.get("last_modified_files", []),
        target_file=state.get("target_file"),
    )

    if not files:
        return {"findings": [], "files_reviewed": state.get("files_reviewed", [])}

    llm = LLMClient.from_env(state["config"])
    loader = StandardsLoader()
    samples = state["config"].review_samples
    findings = _run_review(files, llm, loader, Path(state["target_path"]), samples=samples)

    files_reviewed = list(set(state.get("files_reviewed", []) + [str(f) for f in files]))

    return {
        "findings": findings,
        "files_reviewed": files_reviewed,
    }
```

(This is unchanged except for the new `target_file=state.get("target_file")` argument — included here in full per the no-placeholders rule.)

- [ ] **Step 6: Fix the pre-existing test whose assumptions chunking invalidates**

`test_run_review_sends_full_file_content_past_2000_chars` (already in `tests/test_review_code.py`) currently inspects `mock_llm_client.get_llm.return_value.invoke.call_args` (the *last* call only). With chunking, the marker function and the 60 padding-comment lines become two separate chunks reviewed in two separate calls, and the marker's function chunk is *not* guaranteed to be the last call. Replace the test body's last two lines:

```python
    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    human_content = sent_messages[1].content
    assert marker in human_content
```

with:

```python
    all_calls = mock_llm_client.get_llm.return_value.invoke.call_args_list
    human_contents = [call.args[0][1].content for call in all_calls]
    assert any(marker in content for content in human_contents)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/test_review_code.py -v`
Expected: all PASS, including the previously-failing new tests and the fixed `test_run_review_sends_full_file_content_past_2000_chars`.

- [ ] **Step 8: Run the full suite**

Run: `uv run pytest -v`
Expected: all PASS. (`tests/test_re_review_changed.py` mocks `_run_review` entirely, so it's unaffected by the rewrite; `review_code_node`'s `target_file` argument defaults to `None` via `state.get(...)`, so any test building a `GraphState` literal without that key still works.)

- [ ] **Step 9: Commit**

```bash
git add src/nasa_dod_agent/state.py src/nasa_dod_agent/nodes/review_code.py tests/test_review_code.py
git commit -m "feat(nasa-dod-agent): review per function/chunk instead of per file"
```

---

### Task 4: Chunk-aware fix context, per-chunk retry key, global fix-attempt cap

**Files:**
- Modify: `src/nasa_dod_agent/nodes/generate_fixes.py`
- Modify: `src/nasa_dod_agent/cli.py` (only the `_STOP_MESSAGES` dict — full CLI rewrite is Task 6)
- Test: `tests/test_generate_fixes.py`

**Interfaces:**
- Consumes: `chunk_file` (Task 1); `Finding.function_name`, `RubricConfig.max_fix_attempts_per_chunk`, `RubricConfig.max_total_fix_attempts` (Task 2); `review_code.EXTENSION_LANGUAGES` (existing).
- Produces: `generate_fixes._finding_key` now includes `function_name`; new `stop_reason = "max_total_fix_attempts"`.

- [ ] **Step 1: Update existing tests for the new retry-key format**

`generate_fixes._finding_key` changes from `f"{file_path}::{rule}"` to `f"{file_path}::{function_name}::{rule}"`. Every existing `fix_attempts` dict literal in `tests/test_generate_fixes.py` keyed with the old two-part format must be updated to the new three-part format (since the test findings all have `function_name=None` by default, the new key segment is the literal string `"None"`).

In `tests/test_generate_fixes.py`, update `test_generate_fixes_node_gives_up_after_max_attempts`:

```python
def test_generate_fixes_node_gives_up_after_max_attempts():
    """Regression test: a real run against a weak local model re-reviewed
    already-fixed files and kept reporting the same finding as still
    present, so the agent regenerated patches for it every iteration until
    max_iterations — burning the whole budget on one stuck finding instead
    of stopping and saying so. After max_fix_attempts_per_chunk failed
    attempts at the same (file, function, rule), the agent must stop
    trying and report why instead of spinning until max_iterations.
    """
    finding = _finding(Severity.P0)
    state = make_state([finding], fix_attempts={"a.py::None::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen:
        result = generate_fixes_node(state)

    mock_gen.assert_not_called()
    assert result["patches"] == []
    assert result["stop_reason"] == "max_fix_attempts"
```

Update `test_generate_fixes_node_increments_attempt_count`:

```python
def test_generate_fixes_node_increments_attempt_count():
    finding = _finding(Severity.P0)
    state = make_state([finding])

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    assert result["fix_attempts"] == {"a.py::None::R": 1}
```

Update `test_generate_fixes_node_only_sends_unexhausted_findings_to_llm`:

```python
def test_generate_fixes_node_only_sends_unexhausted_findings_to_llm():
    stuck = Finding(
        severity=Severity.P0, file_path="a.py", line_number=1, rule="R",
        description="D", why_fix="W",
    )
    fresh = Finding(
        severity=Severity.P0, file_path="b.py", line_number=1, rule="S",
        description="D2", why_fix="W2",
    )
    state = make_state([stuck, fresh], fix_attempts={"a.py::None::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert sent_findings == [fresh]
    assert result["fix_attempts"] == {"a.py::None::R": 2, "b.py::None::S": 1}
```

Update `test_generate_patches_includes_real_file_content` — add `function_name="Divide"` to the `Finding(...)` call (the chunk lookup needs to know which function's chunk to show; the fixture's only function is `Divide`):

```python
def test_generate_patches_includes_real_file_content(temp_project):
    """The prompt must show the LLM the actual current content of the
    finding's function, not just the finding's one-line description —
    otherwise the Search block it produces is a guess that won't reliably
    match the real text.
    """
    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0,
        file_path="divide.go",
        line_number=4,
        rule="NASA Rule",
        description="No zero-divisor check",
        why_fix="Panics at runtime on b == 0",
        function_name="Divide",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    _generate_patches([finding], mock_llm_client, temp_project)

    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    human_content = sent_messages[1].content
    assert "func Divide(a, b int) int {" in human_content
    assert "return a / b" in human_content
```

Update `test_generate_patches_feeds_back_previous_failure` similarly — add `function_name="Divide"`:

```python
def test_generate_patches_feeds_back_previous_failure(temp_project):
    """Regression test: a real run kept regenerating the exact same broken
    patch (missing 'import errors') every iteration for 10 iterations,
    because the agent never told the LLM its previous attempt had been
    reverted for a specific reason. The previous patch_errors must reach
    the prompt so the model can avoid repeating the mistake.
    """
    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0,
        file_path="divide.go",
        line_number=4,
        rule="NASA Rule",
        description="No zero-divisor check",
        why_fix="Panics at runtime on b == 0",
        function_name="Divide",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    previous_errors = [
        "Reverted 1 file(s) — patches broke the build: `go build ./...` failed:\n"
        "./divide.go:10:13: undefined: errors"
    ]
    _generate_patches([finding], mock_llm_client, temp_project, previous_errors)

    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    human_content = sent_messages[1].content
    assert "undefined: errors" in human_content
    assert "previous attempt" in human_content
```

(`test_generate_patches_handles_braces_in_finding_text` and `test_generate_patches_prompt_requires_unique_search_block` both use a `target_path` the finding's file doesn't actually exist under, so the existence guard in `_file_contents_context` skips them exactly as before — leave these two tests unchanged.)

- [ ] **Step 2: Write the new failing tests**

Add to `tests/test_generate_fixes.py`:

```python
def test_finding_key_distinguishes_functions_in_same_file():
    """Two distinct functions with the same rule violation in the same
    file must be tracked (and capped) independently — sharing one retry
    budget across unrelated functions would let one stuck function's
    exhaustion block fixing an entirely different one."""
    from nasa_dod_agent.nodes.generate_fixes import _finding_key

    f1 = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D",
        why_fix="W", function_name="Foo",
    )
    f2 = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D",
        why_fix="W", function_name="Bar",
    )
    assert _finding_key(f1) != _finding_key(f2)


def test_generate_fixes_node_stops_at_max_total_fix_attempts():
    """Even if no single chunk has hit its own per-chunk cap, the run
    must stop once the sum of every attempt across every chunk reaches
    max_total_fix_attempts — otherwise a repo with many small findings
    could run an unbounded number of fix calls."""
    findings = [
        Finding(
            severity=Severity.P0, file_path=f"f{i}.py", rule="R",
            description="D", why_fix="W", function_name=f"fn{i}",
        )
        for i in range(3)
    ]
    config = RubricConfig(fix_threshold=1, max_total_fix_attempts=2)
    state = make_state(findings)
    state["config"] = config
    # Two attempts already used up by other findings earlier in the run.
    state["fix_attempts"] = {"other.py::None::X": 2}

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen:
        result = generate_fixes_node(state)

    mock_gen.assert_not_called()
    assert result["patches"] == []
    assert result["stop_reason"] == "max_total_fix_attempts"


def test_generate_fixes_node_trims_batch_to_remaining_total_budget():
    """If only partial budget remains, attempt as many findings as fit
    rather than refusing the whole batch outright."""
    findings = [
        Finding(
            severity=Severity.P0, file_path=f"f{i}.py", rule="R",
            description="D", why_fix="W", function_name=f"fn{i}",
        )
        for i in range(3)
    ]
    config = RubricConfig(fix_threshold=1, max_total_fix_attempts=5)
    state = make_state(findings)
    state["config"] = config
    state["fix_attempts"] = {"other.py::None::X": 4}  # 1 attempt of budget left

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert len(sent_findings) == 1
    assert sum(result["fix_attempts"].values()) == 5


def test_generate_fixes_node_skips_only_the_exhausted_function_in_a_shared_file():
    """Two functions in the SAME file, same rule: one has used up its
    per-chunk budget, the other hasn't. Only the exhausted one should be
    skipped — the sibling function must still get fixed normally."""
    exhausted = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D1",
        why_fix="W", function_name="Foo",
    )
    fresh = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D2",
        why_fix="W", function_name="Bar",
    )
    state = make_state([exhausted, fresh], fix_attempts={"a.go::Foo::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert sent_findings == [fresh]
    assert result["fix_attempts"]["a.go::Foo::R"] == 2
    assert result["fix_attempts"]["a.go::Bar::R"] == 1


def test_chunk_text_for_finding_falls_back_to_whole_file_when_function_gone(temp_project):
    """A finding's function_name might no longer exist by the time a fix
    is attempted (e.g. a prior patch renamed/removed it) — the context
    builder must fall back to the whole file rather than erroring or
    silently showing nothing."""
    from nasa_dod_agent.nodes.generate_fixes import _chunk_text_for_finding

    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0, file_path="divide.go", rule="R", description="D",
        why_fix="W", function_name="NoLongerExists",
    )

    text = _chunk_text_for_finding(finding, target)

    assert text == target.read_text()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_generate_fixes.py -v`
Expected: the three key-format tests fail (`mock_gen.assert_not_called()` fails because the old two-part key doesn't match, so the cap doesn't trigger / `result["fix_attempts"]` has the old-format keys); the two `function_name`-context tests fail on the content assertions (chunk lookup returns the file-level chunk, which lacks the function body, since `_finding_key`/context logic doesn't exist yet); `test_finding_key_distinguishes_functions_in_same_file` fails because the current `_finding_key` ignores `function_name` so both keys are equal; the two new cap tests and the shared-file-skip test fail because `generate_fixes_node` doesn't read the new config fields or key format yet; `test_chunk_text_for_finding_falls_back_to_whole_file_when_function_gone` fails with `ImportError`/`AttributeError` (`_chunk_text_for_finding` doesn't exist yet).

- [ ] **Step 4: Implement the generate_fixes.py changes**

Replace the full contents of `src/nasa_dod_agent/nodes/generate_fixes.py`:

```python
"""Node 3: generate_fixes — ask LLM to produce patches for fixable findings."""

import logging
from pathlib import Path
from typing import List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file
from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding, Patch, PatchError, Severity
from nasa_dod_agent.nodes.review_code import EXTENSION_LANGUAGES
from nasa_dod_agent.state import GraphState

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {Severity.P0: 0, Severity.P1: 1, Severity.P2: 2, Severity.P3: 3}


def _should_fix(finding: Finding, threshold: int) -> bool:
    return SEVERITY_ORDER[finding.severity] <= threshold


def _finding_key(finding: Finding) -> str:
    return f"{finding.file_path}::{finding.function_name}::{finding.rule}"


def _resolve(file_path: str, target_path: Path) -> Path:
    p = Path(file_path)
    return p if p.is_absolute() else target_path / p


def _chunk_text_for_finding(finding: Finding, path: Path) -> str:
    """The exact text of the function (or file-level code) a finding
    belongs to. Falls back to the whole file if the chunk no longer
    exists — e.g. a prior patch renamed/removed the function."""
    language = EXTENSION_LANGUAGES.get(path.suffix, "")
    chunks = chunk_file(path, language)
    target_name = finding.function_name or FILE_LEVEL
    for chunk in chunks:
        if chunk.name == target_name:
            return chunk.text
    return path.read_text()


def _file_contents_context(findings: List[Finding], target_path: Path) -> str:
    """Show the LLM the real, current content of each finding's function
    (or file-level code), not the finding's one-line description — which
    routinely doesn't match exact source text and gives no way to know
    what's already imported or already there.
    """
    context = ""
    seen = set()
    for f in findings:
        key = (f.file_path, f.function_name)
        if key in seen:
            continue
        seen.add(key)
        path = _resolve(f.file_path, target_path)
        if not path.exists():
            continue
        chunk_text = _chunk_text_for_finding(f, path)
        label = f.file_path if f.function_name is None else f"{f.file_path}::{f.function_name}"
        context += f"\n--- {label} ---\n{chunk_text}\n"
    return context


def _generate_patches(
    findings: List[Finding],
    llm_client: LLMClient,
    target_path: Path,
    previous_errors: List[str] | None = None,
) -> Tuple[List[Patch], List[PatchError]]:
    """Call LLM to generate patches for a batch of findings."""
    if not findings:
        return [], []

    findings_text = "\n\n".join(
        f"Finding: {f.description}\n"
        f"File: {f.file_path}\n"
        f"Line: {f.line_number}\n"
        f"Rule: {f.rule}\n"
        f"Why: {f.why_fix}"
        for f in findings
    )
    file_context = _file_contents_context(findings, target_path)

    system = (
        "You are a senior engineer. For each finding, produce a concrete code patch.\n\n"
        "Make the SMALLEST change that resolves the specific finding — nothing else. "
        "Do not change a function's signature, parameter types, or name unless the "
        "finding is literally about that signature. Do not add new dependencies, "
        "concurrency primitives, configurability, or 'production-ready' scaffolding "
        "the finding didn't ask for. Do not leave TODO-style comments or placeholder "
        "logic (e.g. 'should use a proper logger in production') — either implement it "
        "or leave it out. A bigger, cleverer rewrite is a worse patch than a small, "
        "boring one: every extra change you make is new surface area for the next "
        "review pass to flag.\n\n"
        "The Search block MUST be copied verbatim from the file contents shown below — "
        "not reconstructed from memory or the finding's description. If you can't find "
        "exact text to match, say so in the Description instead of guessing.\n\n"
        "The Search block must also be unique: it has to match exactly one location in "
        "the file. If the lines you want to change also appear elsewhere in the file "
        "(e.g. a repeated `if err != nil { ... }` idiom), they are not enough on their "
        "own — include an extra line of surrounding context (the line just before or "
        "after) that differs between the locations, so the block matches only the one "
        "you intend to change.\n\n"
        "If fixing a finding requires changing more than one location in a file (for "
        "example, adding an import AND changing a function body), emit a SEPARATE "
        "### Patch entry for each location — one Search/Replace pair per location.\n\n"
        "Format each patch as:\n"
        "### Patch N: <brief title>\n"
        "**File:** `relative/path/to/file`\n"
        "**Description:** one sentence\n"
        "**Search:**\n```\n<exact text to find>\n```\n"
        "**Replace:**\n```\n<replacement text>\n```\n"
    )
    human = (
        f"Findings to fix:\n\n{findings_text}\n\n"
        f"Current file contents:\n{file_context}"
    )
    if previous_errors:
        errors_text = "\n".join(f"- {e}" for e in previous_errors)
        human += (
            "\n\nA previous attempt at fixing these same findings caused the following "
            "problems — the file contents above are already back to their original state "
            "(those attempts were reverted), but make sure your new patches don't repeat "
            f"the same mistake:\n{errors_text}"
        )

    messages = [SystemMessage(content=system), HumanMessage(content=human)]
    response = llm_client.get_llm().invoke(messages)

    parser = FixParser()
    return parser.parse(response.content)


def generate_fixes_node(state: GraphState) -> dict:
    """Generate patches for findings above the fix threshold, bounded by
    a per-chunk retry cap and a global total-attempts cap."""
    config = state["config"]
    threshold = config.fix_threshold
    fixable = [f for f in state.get("findings", []) if _should_fix(f, threshold)]

    if not fixable:
        # Nothing left to fix at this threshold, but the rubric is still
        # failing (that's the only way we'd get here) — looping further
        # would never change anything, so say so and stop.
        return {"patches": [], "patch_errors": [], "stop_reason": "no_fixable_findings"}

    fix_attempts = dict(state.get("fix_attempts", {}))
    per_chunk_cap = config.max_fix_attempts_per_chunk
    findings = [f for f in fixable if fix_attempts.get(_finding_key(f), 0) < per_chunk_cap]

    if not findings:
        # Every fixable finding has already been retried past its own
        # cap — the model isn't converging on these, so stop instead of
        # spinning through the rest of max_iterations on findings that
        # won't budge.
        return {"patches": [], "patch_errors": [], "stop_reason": "max_fix_attempts"}

    total_attempts_so_far = sum(fix_attempts.values())
    remaining_budget = config.max_total_fix_attempts - total_attempts_so_far
    if remaining_budget <= 0:
        # The whole run has already spent its total fix-attempt budget,
        # even though no single chunk hit its own per-chunk cap — likely
        # many small findings adding up. Stop rather than keep going.
        return {"patches": [], "patch_errors": [], "stop_reason": "max_total_fix_attempts"}
    if len(findings) > remaining_budget:
        findings = findings[:remaining_budget]

    for f in findings:
        key = _finding_key(f)
        fix_attempts[key] = fix_attempts.get(key, 0) + 1
        logger.info(
            "Fixing %s::%s (%s: %s)",
            f.file_path, f.function_name or FILE_LEVEL, f.severity.value, f.description,
        )

    llm = LLMClient.from_env(config)
    target_path = Path(state["target_path"])
    previous_errors = state.get("patch_errors", [])
    patches, parse_errors = _generate_patches(findings, llm, target_path, previous_errors)

    return {
        "patches": patches,
        "patch_errors": [f"{e.file_path}: {e.error_message}" for e in parse_errors],
        "fix_attempts": fix_attempts,
    }
```

- [ ] **Step 5: Add the new stop message to the CLI**

In `src/nasa_dod_agent/cli.py`, add a new entry to `_STOP_MESSAGES` (currently lines 41–56), after the `"max_fix_attempts"` entry:

```python
    "max_fix_attempts": (
        "Rubric NOT met — gave up on one or more findings after repeated "
        "failed fix attempts (the model kept producing patches that didn't "
        "resolve them). These likely need manual review."
    ),
    "max_total_fix_attempts": (
        "Rubric NOT met — hit the total fix-attempt budget for this run "
        "(max_total_fix_attempts in config.yaml). Re-run to continue "
        "fixing the rest, or raise the budget."
    ),
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_generate_fixes.py -v`
Expected: all PASS.

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/nasa_dod_agent/nodes/generate_fixes.py src/nasa_dod_agent/cli.py tests/test_generate_fixes.py
git commit -m "feat(nasa-dod-agent): per-chunk retry key, global fix-attempt cap, chunk-aware fix context"
```

---

### Task 5: Progress logging in `apply_fixes_node`

**Files:**
- Modify: `src/nasa_dod_agent/nodes/apply_fixes.py`
- Test: `tests/test_apply_fixes.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new (logging only).

- [ ] **Step 1: Read the existing test file's imports/fixtures**

Run: `uv run pytest tests/test_apply_fixes.py -v` to confirm the current 8 tests pass before changing anything (baseline).

- [ ] **Step 2: Write the failing test**

Add to `tests/test_apply_fixes.py` (match the existing file's import style — it already imports `Patch` and `apply_fixes_node`; add `caplog` as a test parameter, no new imports needed):

```python
def test_apply_fixes_logs_which_file_is_being_patched(temp_project, caplog):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")

    patch_obj = Patch(
        file_path=str(target), description="d", search_block="x = 1", replace_block="x = 2"
    )
    state = {"target_path": str(temp_project), "patches": [patch_obj], "patch_errors": []}

    caplog.set_level("INFO")
    apply_fixes_node(state)

    assert "main.py" in caplog.text
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/test_apply_fixes.py -k logs_which_file -v`
Expected: FAIL — `assert "main.py" in caplog.text` with `caplog.text == ""` (nothing logged yet).

- [ ] **Step 4: Implement the logging**

In `src/nasa_dod_agent/nodes/apply_fixes.py`, add the import and logger after the existing imports (currently lines 1–9):

```python
"""Node 4: apply_fixes — atomically apply patches to disk with backups."""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.state import GraphState

logger = logging.getLogger(__name__)

_BUILD_TIMEOUT_SECONDS = 60
```

Then in `apply_fixes_node`'s patch loop (currently lines 110–134), add one log line right after the existence check:

```python
    for patch in patches:
        try:
            file_path = Path(patch.file_path)
            if not file_path.is_absolute():
                file_path = target_path / file_path
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                continue

            logger.info("Applying patch to %s", file_path.name)

            # Back up only on this file's first patch in the batch — a
            # second patch to the same file must not overwrite the backup
            # with already-modified content, or a revert would restore the
            # post-first-patch state instead of the pristine original.
            if str(file_path) not in backup_for:
                local_backup = backup_dir / (file_path.name + ".bak")
                local_backup.write_bytes(file_path.read_bytes())
                backup_paths.append(str(local_backup))
                backup_for[str(file_path)] = local_backup

            parser.apply_patch(patch, file_path)

            if str(file_path) not in files_modified:
                files_modified.append(str(file_path))
        except Exception as e:
            errors.append(str(e))
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_apply_fixes.py -v`
Expected: all 9 tests PASS (8 existing + 1 new).

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/nasa_dod_agent/nodes/apply_fixes.py tests/test_apply_fixes.py
git commit -m "feat(nasa-dod-agent): log which file apply_fixes is patching"
```

---

### Task 6: CLI single-file targeting and global logging setup

**Files:**
- Modify: `src/nasa_dod_agent/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `GraphState.target_file` (Task 3).
- Produces: `review`/`restore`/`status` commands accept a file path, not just a directory.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`:

```python
from nasa_dod_agent.cli import status


def test_review_accepts_a_single_file_path(temp_project):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")

    runner = CliRunner()
    result = runner.invoke(main, ["review", str(target), "--no-interactive"])

    # Fails fast on the missing OPENAI_API_KEY check rather than on Click's
    # own path validation — proves Click accepted a file path argument.
    assert "OPENAI_API_KEY" in result.output
    assert (temp_project / ".nasa-dod-agent").exists()


def test_restore_accepts_a_single_file_path(temp_project):
    target = temp_project / "main.py"
    target.write_text("original\n")
    backup_dir = temp_project / ".nasa-dod-agent" / "backups"
    backup_dir.mkdir(parents=True)
    (backup_dir / "main.py.bak").write_text("backup content\n")

    runner = CliRunner()
    result = runner.invoke(restore, [str(target)])

    assert result.exit_code == 0
    assert "backup content" in target.read_text()


def test_status_accepts_a_single_file_path(temp_project):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")
    state_dir = temp_project / ".nasa-dod-agent"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text('{"iteration": 3, "p0_count": 1}')

    runner = CliRunner()
    result = runner.invoke(status, [str(target)])

    assert result.exit_code == 0
    assert "Iteration: 3" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v -k "single_file"`
Expected: all three FAIL with Click usage errors (`Error: Invalid value for 'PATH': '...' is a file.`), since `file_okay=False` currently rejects file arguments.

- [ ] **Step 3: Implement the CLI changes**

Replace `src/nasa_dod_agent/cli.py` in full:

```python
"""Click CLI entry point for nasa-dod-agent."""

import logging
import os
import shutil
from pathlib import Path

import click
from pydantic import ValidationError

from nasa_dod_agent.config import ConfigLoader
from nasa_dod_agent.graph import build_graph
from nasa_dod_agent.state import GraphState


def _archive_checkpoints(checkpoint_dir: Path) -> None:
    """Move everything in checkpoint_dir into checkpoint_dir/archive/.

    Uses copy-then-delete rather than ``shutil.move`` so it also works
    when the destination is on a different filesystem (e.g. in tests).
    """
    if not checkpoint_dir.exists():
        return

    archive = checkpoint_dir / "archive"
    archive.mkdir(parents=True, exist_ok=True)

    for item in checkpoint_dir.iterdir():
        if item.name == "archive":
            continue
        dest = archive / item.name
        if dest.exists():
            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
        if item.is_dir():
            shutil.copytree(item, dest)
            shutil.rmtree(item)
        else:
            shutil.copy2(item, dest)
            item.unlink()


def _target_dir(project_path: Path) -> Path:
    """Where .nasa-dod-agent/ lives: the path itself if it's a directory,
    or its parent directory if it's a single file."""
    return project_path.parent if project_path.is_file() else project_path


_STOP_MESSAGES = {
    "rubric_passed": "Rubric passed: YES",
    "max_iterations": (
        "Rubric NOT met — hit max_iterations without converging. "
        "Findings still exceed the configured thresholds."
    ),
    "no_fixable_findings": (
        "Rubric NOT met — no fixable findings. Remaining findings are all "
        "below fix_threshold. Adjust fix_threshold or max_pX in config.yaml."
    ),
    "max_fix_attempts": (
        "Rubric NOT met — gave up on one or more findings after repeated "
        "failed fix attempts (the model kept producing patches that didn't "
        "resolve them). These likely need manual review."
    ),
    "max_total_fix_attempts": (
        "Rubric NOT met — hit the total fix-attempt budget for this run "
        "(max_total_fix_attempts in config.yaml). Re-run to continue "
        "fixing the rest, or raise the budget."
    ),
}


def _stop_message(stop_reason: str | None) -> str:
    return _STOP_MESSAGES.get(stop_reason, "Rubric NOT met.")


@click.group()
def main():
    """NASA/DoD Deep Agent — iterative code review with auto-fix."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
@click.option("--full", is_flag=True, help="Force full scan, ignore checkpoints")
@click.option("--max-rounds", type=int, default=None, help="Override max_iterations")
@click.option("--dry-run", is_flag=True, help="Generate fixes but don't write")
@click.option("--reset", is_flag=True, help="Delete checkpoint, start fresh")
@click.option("--no-interactive", is_flag=True, help="Skip resume prompt")
def review(path, full, max_rounds, dry_run, reset, no_interactive):
    """Run the NASA/DOD review loop on a directory or a single file."""
    project_path = Path(path)
    target_dir = _target_dir(project_path)
    target_file = str(project_path.absolute()) if project_path.is_file() else None
    config_dir = target_dir / ".nasa-dod-agent"
    checkpoint_dir = str(config_dir / "checkpoints")

    checkpoint_exists = (
        (config_dir / "checkpoints").exists()
        and any((config_dir / "checkpoints").iterdir())
    )

    if reset:
        _archive_checkpoints(config_dir / "checkpoints")
        click.echo("Checkpoint reset. Starting fresh.")

    elif checkpoint_exists and not no_interactive and not full:
        click.echo("In-progress review found for this directory.")
        click.echo("Use --reset to start fresh or --no-interactive to resume silently.")
        return

    try:
        config = ConfigLoader.load(target_dir)
    except ValidationError as e:
        click.echo(f"Invalid {config_dir / 'config.yaml'}:")
        for err in e.errors():
            field = ".".join(str(p) for p in err["loc"])
            click.echo(f"  {field}: {err['msg']} (got {err.get('input')!r})")
        raise click.Abort()

    if config is None:
        config = ConfigLoader.init_config(target_dir)
        click.echo(f"Created default config at {config_dir / 'config.yaml'}")

    if max_rounds is not None:
        config.max_iterations = max_rounds

    if not os.environ.get("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY environment variable is required")
        raise click.Abort()

    state: GraphState = {
        "target_path": str(target_dir.absolute()),
        "target_file": target_file,
        "review_mode": "full" if full or not checkpoint_exists else "incremental",
        "iteration": 0,
        "max_iterations": config.max_iterations,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "fix_attempts": {},
        "config": config,
        "rubric_passed": False,
        "stop_reason": None,
        "p0_count": 0,
        "p1_count": 0,
        "p2_count": 0,
        "p3_count": 0,
        "patches": [],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
    }

    graph = build_graph(checkpoint_dir)
    thread_id = f"review-{project_path.name}"
    final_state = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})

    click.echo("\n--- Review Complete ---")
    click.echo(f"Iterations: {final_state['iteration']}")
    click.echo(
        f"P0: {final_state['p0_count']}  P1: {final_state['p1_count']}  "
        f"P2: {final_state['p2_count']}  P3: {final_state['p3_count']}"
    )
    click.echo(_stop_message(final_state.get("stop_reason")))
    if final_state.get("patch_errors"):
        click.echo(f"Patch errors: {len(final_state['patch_errors'])}")
        for err in final_state["patch_errors"]:
            click.echo(f"  - {err}")

    _archive_checkpoints(config_dir / "checkpoints")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
def restore(path):
    """Undo all agent changes (restore .bak files)."""
    project_path = _target_dir(Path(path))
    backup_dir = project_path / ".nasa-dod-agent" / "backups"

    if not backup_dir.exists():
        click.echo("No backups found.")
        return

    count = 0
    for backup in backup_dir.glob("*.bak"):
        original_name = backup.stem
        candidates = list(project_path.rglob(original_name))
        candidates = [c for c in candidates if ".nasa-dod-agent" not in str(c)]
        if candidates:
            original = candidates[0]
            original.write_bytes(backup.read_bytes())
            count += 1
            click.echo(f"Restored {original}")

    click.echo(f"Restored {count} file(s).")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=True))
def status(path):
    """Show current review state."""
    project_path = _target_dir(Path(path))
    state_file = project_path / ".nasa-dod-agent" / "state.json"
    if state_file.exists():
        import json
        data = json.loads(state_file.read_text())
        click.echo(f"Current review state for {project_path}:")
        click.echo(f"  Iteration: {data.get('iteration', 'N/A')}")
        click.echo(f"  P0: {data.get('p0_count', 0)}")
        click.echo(f"  P1: {data.get('p1_count', 0)}")
        click.echo(f"  {_stop_message(data.get('stop_reason'))}")
    else:
        click.echo("No active review state found.")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def init_config(path):
    """Generate a default config.yaml."""
    project_path = Path(path)
    ConfigLoader.init_config(project_path)
    click.echo(f"Created default config at {project_path / '.nasa-dod-agent' / 'config.yaml'}")


if __name__ == "__main__":
    main()
```

(`init_config` is deliberately left directory-only — the spec only calls for file targeting on `review`/`restore`/`status`, and `review` already auto-creates config in the right directory for a file target via `_target_dir`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: all PASS, including the 3 new tests.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/nasa_dod_agent/cli.py tests/test_cli.py
git commit -m "feat(nasa-dod-agent): accept a single file as the review/restore/status target"
```

---

### Task 7: Manual end-to-end verification

**Files:** none (verification only, no code changes).

- [ ] **Step 1: Verify console logging is visible during a real run**

Run (from `/home/code/development/ai/agents/nasa-dod-agent`, with `OPENAI_API_KEY`/`OPENAI_BASE_URL`/`OPENAI_MODEL` already exported in the shell, as in earlier sessions):

```bash
uv run nasa-dod-agent review --reset ../../../nasa-dod-go-sample/
```

Expected: console shows lines like `Reviewing divide.go (1 function)`, `  └─ Divide`, `Fixing divide.go::Divide (...)`, `Applying patch to divide.go` interleaved with the existing `--- Review Complete ---` summary — confirming Task 3/4/5's logging is wired end-to-end through a real graph run.

- [ ] **Step 2: Verify single-file targeting**

Run:

```bash
uv run nasa-dod-agent review --reset ../../../nasa-dod-go-sample/divide.go
```

Expected: only `divide.go` is reviewed (console shows exactly one `Reviewing divide.go (...)` line, no other files); `.nasa-dod-agent/` is created inside `nasa-dod-go-sample/` (the file's parent directory), not anywhere else.

- [ ] **Step 3: Verify the iseven duplicate-function finding survives chunking**

Run:

```bash
uv run nasa-dod-agent review --reset ../../../iseven/
```

Expected: console shows `Reviewing test/iseven_test.go (N functions)` with each function name logged individually; the duplicate-`TestIsEven_maxUint` finding from earlier in this session is found again (not silently lost to chunk boundaries splitting the two occurrences into unreviewed pieces) — check the final P0/P1/P2/P3 counts are nonzero, not the `Rubric passed: YES` / all-zero result from before the truncation/batching fixes.

- [ ] **Step 4: Report results**

Summarize what was observed in each of the three runs above (exact console output highlights, final iteration/severity counts, any unexpected errors) back to the user before considering this plan complete.
