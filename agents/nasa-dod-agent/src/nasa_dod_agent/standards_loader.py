"""Load vendored NASA/DOD skill markdown into prompts."""

from pathlib import Path
from typing import Optional


class StandardsLoader:
    """Loads bundled skill markdown files."""

    def __init__(self, standards_dir: Optional[Path] = None):
        if standards_dir is None:
            # Relative to this file: src/nasa_dod_agent/ -> ../../standards/
            # __file__ is in src/nasa_dod_agent/, so parent.parent.parent = project root
            self.standards_dir = Path(__file__).parent.parent.parent / "standards"
        else:
            self.standards_dir = standards_dir

    def _load(self, filename: str) -> str:
        path = self.standards_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Standards file not found: {path}")
        return path.read_text()

    def get_reviewer_prompt(self) -> str:
        return self._load("reviewer-prompt.md")

    def get_severity_guide(self) -> str:
        return self._load("severity-guide.md")

    def build_system_prompt(self, languages: list[str]) -> str:
        """Build the full system prompt for a review pass."""
        reviewer = self.get_reviewer_prompt()
        severity = self.get_severity_guide()
        return (
            f"You are a senior engineer conducting a NASA/DOD-grade code review.\n\n"
            f"Reviewer Instructions:\n{reviewer}\n\n"
            f"Severity Guide:\n{severity}\n\n"
            f"Languages detected: {', '.join(languages)}\n"
        )
