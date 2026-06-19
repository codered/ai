"""TypedDict definition for the LangGraph state."""

from typing import List, Optional, TypedDict

from nasa_dod_agent.models import Finding, Patch, PatchError, RubricConfig


class GraphState(TypedDict):
    target_path: str
    review_mode: str  # "full" or "incremental"
    iteration: int
    max_iterations: int

    findings: List[Finding]
    files_reviewed: List[str]
    last_modified_files: List[str]

    config: RubricConfig
    rubric_passed: bool
    # Why the loop stopped: "rubric_passed", "max_iterations", or
    # "no_fixable_findings" (remaining findings are all below fix_threshold,
    # so no patches were ever generated for them). None while still running.
    stop_reason: Optional[str]
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int

    patches: List[Patch]
    patch_errors: List[PatchError]
    files_modified: List[str]
    backup_paths: List[str]
