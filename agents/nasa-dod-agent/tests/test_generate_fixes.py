from unittest.mock import patch, MagicMock
from nasa_dod_agent.nodes.generate_fixes import generate_fixes_node
from nasa_dod_agent.models import Finding, Severity, Patch, RubricConfig

def make_state(findings):
    return {
        "target_path": ".",
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": findings,
        "files_reviewed": [],
        "last_modified_files": [],
        "config": RubricConfig(fix_threshold=1),
        "rubric_passed": False,
        "patches": [],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }

def test_generates_patches_for_fixable_findings():
    f = Finding(severity=Severity.P1, file_path="a.py", line_number=1, rule="R", description="D", why_fix="W")
    state = make_state([f])

    mock_patch = Patch(file_path="a.py", description="fix", search_block="x", replace_block="y")
    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = [mock_patch]
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    assert len(result["patches"]) == 1
    assert result["patches"][0].file_path == "a.py"

def test_no_fixes_for_p3_only():
    f = Finding(severity=Severity.P3, file_path="a.py", line_number=1, rule="R", description="D", why_fix="W")
    state = make_state([f])
    result = generate_fixes_node(state)
    assert result["patches"] == []
