from unittest.mock import MagicMock, patch

from nasa_dod_agent.models import Finding, Severity
from nasa_dod_agent.nodes.re_review_changed import re_review_changed_node


def test_re_review_reads_changed_files(temp_project):
    target = temp_project / "main.py"
    target.write_text("y = 2\n")

    state = {
        "target_path": str(temp_project),
        "review_mode": "incremental",
        "iteration": 1,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": None,
        "rubric_passed": False,
        "patches": [],
        "patch_errors": [],
        "files_modified": [str(target)],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }

    mock_client = MagicMock()
    with patch("nasa_dod_agent.nodes.re_review_changed._run_review") as mock, \
         patch("nasa_dod_agent.nodes.re_review_changed.LLMClient") as mock_llm:
        mock.return_value = []
        mock_llm.from_env.return_value = mock_client
        result = re_review_changed_node(state)

    assert "findings" in result
    mock.assert_called_once()

def test_empty_files_modified_returns_existing_findings():
    state = {
        "target_path": ".",
        "review_mode": "incremental",
        "iteration": 1,
        "max_iterations": 10,
        "findings": [
            Finding(
                severity=Severity.P2,
                file_path="old.py",
                line_number=1,
                rule="R",
                description="D",
                why_fix="W",
            )
        ],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": None,
        "rubric_passed": False,
        "patches": [],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = re_review_changed_node(state)
    assert len(result["findings"]) == 1
