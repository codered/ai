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


class Patch(BaseModel):
    """A concrete code patch to apply."""
    file_path: str
    description: str = Field(..., description="What this patch does")
    search_block: str = Field(..., description="Text to find in the file")
    replace_block: str = Field(..., description="Text to replace with")
    context_before: Optional[str] = Field(
        None, description="Expected lines before search_block"
    )
    context_after: Optional[str] = Field(
        None, description="Expected lines after search_block"
    )


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
    max_iterations: int = Field(default=10, ge=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class PatchError(BaseModel):
    """Record of a patch that failed to parse or apply."""
    file_path: str
    description: str
    error_message: str


class FindingsReport(BaseModel):
    """Complete report from a review pass."""
    findings: List[Finding] = Field(default_factory=list)
    files_reviewed: List[str] = Field(default_factory=list)
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
