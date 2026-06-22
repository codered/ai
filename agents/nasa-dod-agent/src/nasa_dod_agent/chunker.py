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
