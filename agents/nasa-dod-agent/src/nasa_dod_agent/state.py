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
    # Set when the CLI was pointed at a single file rather than a
    # directory — when present, review_code._collect_files returns just
    # this file instead of globbing target_path.
    target_file: Optional[str]
    # Count of fix attempts per finding, keyed by
    # "{file_path}::{function_name}::{rule}".
    # Accumulates across the whole run (never reset per-iteration), so a
    # finding that keeps coming back after being patched (e.g. the review
    # model gives inconsistent verdicts) can be capped instead of retried
    # every iteration until max_iterations.
    fix_attempts: dict[str, int]

    config: RubricConfig
    rubric_passed: bool
    # Why the loop stopped: "rubric_passed", "max_iterations",
    # "no_fixable_findings" (remaining findings are all below fix_threshold,
    # so no patches were ever generated for them), "max_fix_attempts"
    # (every fixable finding hit its own per-chunk retry cap without
    # resolving — config-driven via RubricConfig.max_fix_attempts_per_chunk,
    # not a hardcoded constant), or "max_total_fix_attempts" (the run's
    # total fix-attempt budget across every chunk/file/iteration was
    # exhausted, per RubricConfig.max_total_fix_attempts). None while still
    # running.
    stop_reason: Optional[str]
    p0_count: int
    p1_count: int
    p2_count: int
    p3_count: int

    patches: List[Patch]
    patch_errors: List[PatchError]
    files_modified: List[str]
    backup_paths: List[str]
