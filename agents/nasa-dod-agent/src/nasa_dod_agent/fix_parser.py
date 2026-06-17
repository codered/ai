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

    def apply_patch(self, patch: Patch) -> None:
        """Apply a single patch to disk. Creates .bak backup first."""
        path = Path(patch.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Patch target not found: {path}")

        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_bytes(path.read_bytes())

        content = path.read_text()
        if patch.search_block not in content:
            raise ValueError(f"Search block not found in {path}")

        new_content = content.replace(patch.search_block, patch.replace_block, 1)
        path.write_text(new_content)
