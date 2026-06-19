from nasa_dod_agent.models import Finding, RubricConfig, Severity
from nasa_dod_agent.nodes.evaluate_rubric import evaluate_rubric_node


def _finding(severity):
    return Finding(
        severity=severity, file_path="a.py", line_number=1, rule="R", description="D", why_fix="W"
    )


def make_state(findings, config=None):
    config = config or RubricConfig(max_p0=0, max_p1=2)
    return {
        "target_path": ".",
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": findings,
        "files_reviewed": [],
        "last_modified_files": [],
        "config": config,
        "rubric_passed": False,
        "p0_count": 0,
        "p1_count": 0,
        "p2_count": 0,
        "p3_count": 0,
        "patches": [],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
    }

def test_rubric_passes_when_all_below_threshold():
    state = make_state([_finding(Severity.P2)])
    result = evaluate_rubric_node(state)
    assert result["rubric_passed"] is True
    assert result["stop_reason"] == "rubric_passed"
    assert result["p2_count"] == 1

def test_rubric_fails_on_p0():
    state = make_state([_finding(Severity.P0)])
    result = evaluate_rubric_node(state)
    assert result["rubric_passed"] is False
    assert result["stop_reason"] is None
    assert result["p0_count"] == 1

def test_iteration_max_does_not_fake_a_pass():
    """Hitting max_iterations must not be reported as a genuine rubric pass."""
    config = RubricConfig(max_p0=0, max_p1=2, max_iterations=1)
    state = make_state([_finding(Severity.P0)], config=config)
    state["iteration"] = 1
    result = evaluate_rubric_node(state)
    assert result["rubric_passed"] is False
    assert result["stop_reason"] == "max_iterations"
