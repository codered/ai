from nasa_dod_agent.graph import should_apply_fixes, should_continue
from nasa_dod_agent.models import Finding, RubricConfig, Severity


def test_should_continue_passes():
    state = {
        "target_path": ".",
        "review_mode": "full",
        "iteration": 1,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": RubricConfig(),
        "rubric_passed": True,
        "patches": [],
        "backup_paths": [],
        "patch_errors": [],
        "files_modified": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = should_continue(state)
    assert result == "end"

def test_should_continue_fails():
    state = {
        "target_path": ".",
        "review_mode": "full",
        "iteration": 1,
        "max_iterations": 10,
        "findings": [
            Finding(
                severity=Severity.P0,
                file_path="a.py",
                line_number=1,
                rule="R",
                description="D",
                why_fix="W",
            )
        ],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": RubricConfig(),
        "rubric_passed": False,
        "patches": [],
        "backup_paths": [],
        "patch_errors": [],
        "files_modified": [],
        "p0_count": 1, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = should_continue(state)
    assert result == "generate_fixes"

def test_should_continue_stops_at_max_iterations_even_if_not_passed():
    state = {
        "target_path": ".",
        "review_mode": "full",
        "iteration": 10,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": RubricConfig(),
        "rubric_passed": False,
        "patches": [],
        "backup_paths": [],
        "patch_errors": [],
        "files_modified": [],
        "p0_count": 1, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = should_continue(state)
    assert result == "end"

def test_should_apply_fixes_when_patches_exist():
    state = {"stop_reason": None, "patches": ["a patch"]}
    assert should_apply_fixes(state) == "apply_fixes"

def test_should_apply_fixes_stops_when_no_fixable_findings():
    state = {"stop_reason": "no_fixable_findings", "patches": []}
    assert should_apply_fixes(state) == "end"

def test_should_apply_fixes_stops_when_fix_attempts_exhausted():
    state = {"stop_reason": "max_fix_attempts", "patches": []}
    assert should_apply_fixes(state) == "end"
