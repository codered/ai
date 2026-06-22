"""Pydantic v2 models for the NASA/DoD review agent."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """NASA/DOD severity levels."""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class FixOption(BaseModel):
    """One concrete fix option with trade-offs."""
    label: str = Field(..., description="Short label")
    description: str = Field(..., description="Explanation")
    code: Optional[str] = Field(None, description="Code snippet")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    recommended: bool = False


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


class Patch(BaseModel):
    """A concrete code patch to apply."""
    file_path: str
    description: str = Field(..., description="What this patch does")
    search_block: str = Field(..., description="Text to find in the file")
    replace_block: str = Field(..., description="Text to replace with")


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
            "only reports on some of its attempts. This multiplies against "
            "BOTH layers of calls _run_review makes per file: once per "
            "per-function chunk, AND once more for the whole-file "
            "cross-function pass (skipped only when the file has 1 or "
            "fewer chunks) — so the number of LLM calls for a file scales "
            "as review_samples * (functions_in_file + 1), not just "
            "file count. Raise this with care on large, many-function "
            "files."
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


class PatchError(BaseModel):
    """Record of a patch that failed to parse or apply."""
    file_path: str
    description: str
    error_message: str
