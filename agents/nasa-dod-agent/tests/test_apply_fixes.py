from pathlib import Path
from nasa_dod_agent.nodes.apply_fixes import apply_fixes_node
from nasa_dod_agent.models import Patch

def test_apply_fixes_creates_backup(temp_project):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")

    state = {
        "target_path": str(temp_project),
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": None,
        "rubric_passed": False,
        "patches": [Patch(file_path=str(target), description="fix", search_block="x = 1", replace_block="y = 2")],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }

    result = apply_fixes_node(state)

    assert target.read_text() == "y = 2\n"
    assert (temp_project / ".nasa-dod-agent" / "backups" / "main.py.bak").exists()
    assert str(target) in result["files_modified"]

def test_no_patches_returns_empty(temp_project):
    state = {
        "target_path": str(temp_project),
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": [],
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
    result = apply_fixes_node(state)
    assert result["files_modified"] == []

def test_missing_file_records_error(temp_project):
    state = {
        "target_path": str(temp_project),
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": None,
        "rubric_passed": False,
        "patches": [Patch(file_path="/nonexistent/file.py", description="fix", search_block="x", replace_block="y")],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = apply_fixes_node(state)
    assert len(result["patch_errors"]) == 1
    assert "File not found" in result["patch_errors"][0]
