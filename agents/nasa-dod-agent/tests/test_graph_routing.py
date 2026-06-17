from nasa_dod_agent.graph import should_continue
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
        "findings": [Finding(severity=Severity.P0, file_path="a.py", line_number=1, rule="R", description="D", why_fix="W")],
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
