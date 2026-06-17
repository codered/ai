from unittest.mock import MagicMock, patch
from nasa_dod_agent.nodes.review_code import review_code_node
from nasa_dod_agent.state import GraphState
from nasa_dod_agent.models import Finding, Severity


def test_review_code_node_collects_findings(temp_project):
    target_file = temp_project / "main.py"
    target_file.write_text("while True:\n    pass\n")

    state: GraphState = {
        "target_path": str(temp_project),
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": MagicMock(max_p0=0, max_p1=2),
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

    mock_finding = Finding(
        severity=Severity.P0,
        file_path="main.py",
        line_number=1,
        rule="NASA Rule 2",
        description="Unbounded loop",
        why_fix="System hang risk",
    )

    with (
        patch("nasa_dod_agent.nodes.review_code._run_review") as mock_review,
        patch("nasa_dod_agent.nodes.review_code.LLMClient") as mock_llm_client,
    ):
        mock_review.return_value = [mock_finding]
        result = review_code_node(state)

    assert len(result["findings"]) == 1
    assert result["findings"][0].severity == Severity.P0
    assert any("main.py" in f for f in result["files_reviewed"])
