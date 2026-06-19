"""Parse LLM-generated patch descriptions into structured Patch objects."""

import re
from pathlib import Path
from typing import List, Tuple

from nasa_dod_agent.models import Patch, PatchError


class FixParser:
    """Parses markdown-style patch blocks from LLM output."""

    def parse(self, raw: str) -> Tuple[List[Patch], List[PatchError]]:
        """Extract Patch objects from LLM markdown output."""
        patches: List[Patch] = []
        errors: List[PatchError] = []

        blocks = re.split(r"(?=###\s*Patch)", raw)
        for block in blocks:
            if not block.strip().startswith("###"):
                continue
            patch = self._parse_single(block)
            if patch:
                patches.append(patch)
            else:
                errors.append(
                    PatchError(
                        file_path="unknown",
                        description=block[:100],
                        error_message="Failed to parse patch block",
                    )
                )
        return patches, errors

    def _parse_single(self, block: str) -> Patch | None:
        file_match = re.search(r"\*\*File:\*\*\s*`?([^`\n]+)`?", block)
        if not file_match:
            return None
        file_path = file_match.group(1).strip()

        desc_match = re.search(
            r"\*\*Description:\*\*\s*(.+?)(?=\*\*Search|\*\*Replace|$)",
            block,
            re.DOTALL,
        )
        description = desc_match.group(1).strip() if desc_match else ""

        search = self._extract_code_block(block, "Search")
        replace = self._extract_code_block(block, "Replace")

        if not search or not replace:
            return None

        return Patch(
            file_path=file_path,
            description=description or "Auto-generated fix",
            search_block=search,
            replace_block=replace,
        )

    def _extract_code_block(self, block: str, label: str) -> str | None:
        pattern = rf"\*\*{label}:\*\*\s*(?:\n+)?```\w*\n(.*?)```"
        match = re.search(pattern, block, re.DOTALL)
        if match:
            return match.group(1).rstrip()
        pattern2 = rf"\*\*{label}:\*\*\s*(.*?)\n\*(\*\w+:|###|$)"
        match2 = re.search(pattern2, block, re.DOTALL)
        if match2:
            return match2.group(1).strip()
        return None

    def apply_patch(self, patch: Patch, path: Path | None = None) -> None:
        """Apply a single patch to disk.

        ``path`` is the resolved location to write to. Pass it explicitly
        when ``patch.file_path`` is relative to the reviewed project rather
        than to the process's current directory (see ``apply_fixes_node``).
        Backups are the caller's responsibility — this method only writes.
        """
        if path is None:
            path = Path(patch.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Patch target not found: {path}")

        content = path.read_text()
        match_count = content.count(patch.search_block)
        if match_count == 0:
            raise ValueError(f"Search block not found in {path}")
        if match_count > 1:
            raise ValueError(
                f"Search block matches {match_count} locations in {path}; "
                "refusing to guess which one the LLM meant — add more "
                "surrounding context (e.g. a preceding line that differs "
                "between the locations) so the Search block is unique"
            )

        start = content.index(patch.search_block)
        end = start + len(patch.search_block)
        if _cuts_mid_token(content, start, end, patch.search_block):
            raise ValueError(
                f"Search block in {path} is truncated mid-identifier (the LLM cut it "
                "off early) — applying it would splice code apart instead of replacing "
                "a clean unit, so refusing rather than corrupting the file"
            )

        new_content = content[:start] + patch.replace_block + content[end:]
        path.write_text(new_content)


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _cuts_mid_token(content: str, start: int, end: int, search_block: str) -> bool:
    """True if the match's edges fall inside an identifier/word.

    A clean search block starts/ends on a token boundary. If the character
    right before the match continues the same word as the match's first
    character (or likewise after the match), the LLM truncated the block
    mid-token rather than giving us a complete line/statement.
    """
    if not search_block:
        return False
    starts_mid_word = (
        _is_word_char(search_block[0]) and start > 0 and _is_word_char(content[start - 1])
    )
    ends_mid_word = (
        _is_word_char(search_block[-1]) and end < len(content) and _is_word_char(content[end])
    )
    return starts_mid_word or ends_mid_word
