"""TypedDict definition for the LangGraph state."""

from typing import List, TypedDict

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
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int

    patches: List[Patch]
    patch_errors: List[PatchError]
    files_modified: List[str]
    backup_paths: List[str]
