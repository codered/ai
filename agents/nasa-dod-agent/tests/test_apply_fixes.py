import shutil

import pytest

from nasa_dod_agent.models import Patch
from nasa_dod_agent.nodes.apply_fixes import apply_fixes_node


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
        "patches": [
            Patch(
                file_path=str(target),
                description="fix",
                search_block="x = 1",
                replace_block="y = 2",
            )
        ],
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
        "patches": [
            Patch(
                file_path="/nonexistent/file.py",
                description="fix",
                search_block="x",
                replace_block="y",
            )
        ],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }
    result = apply_fixes_node(state)
    assert len(result["patch_errors"]) == 1
    assert "File not found" in result["patch_errors"][0]


def _state_with_patches(temp_project, patches):
    return {
        "target_path": str(temp_project),
        "review_mode": "full",
        "iteration": 0,
        "max_iterations": 10,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": None,
        "rubric_passed": False,
        "patches": patches,
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
        "p0_count": 0, "p1_count": 0, "p2_count": 0, "p3_count": 0,
    }


def test_reverts_patch_that_breaks_python_syntax(temp_project):
    """A patch that's individually well-formed text but leaves the file
    syntactically broken must be rolled back, not left on disk."""
    target = temp_project / "main.py"
    target.write_text("def f():\n    return 1\n")

    state = _state_with_patches(temp_project, [
        Patch(
            file_path=str(target),
            description="break it",
            search_block="return 1",
            replace_block="return (",  # unbalanced paren -> syntax error
        )
    ])

    result = apply_fixes_node(state)

    assert target.read_text() == "def f():\n    return 1\n"
    assert result["files_modified"] == []
    assert any("broke the build" in e for e in result["patch_errors"])


@pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")
def test_reverts_incomplete_go_patch(temp_project):
    """Regression test: a real run patched a function's return type to add
    an error value but didn't update every return statement, leaving the
    file with 'not enough return values' — individually valid text, but an
    incomplete edit. This must be caught and reverted, not left broken.
    """
    (temp_project / "go.mod").write_text("module sample\n\ngo 1.21\n")
    target = temp_project / "readconfig.go"
    target.write_text(
        "package sample\n\n"
        "func ReadConfig() []byte {\n"
        "\tdata := make([]byte, 1024)\n"
        "\treturn data\n"
        "}\n"
    )
    original = target.read_text()

    state = _state_with_patches(temp_project, [
        Patch(
            file_path=str(target),
            description="add error return",
            search_block="func ReadConfig() []byte {",
            replace_block="func ReadConfig() ([]byte, error) {",
        )
    ])

    result = apply_fixes_node(state)

    assert target.read_text() == original
    assert result["files_modified"] == []
    assert any("broke the build" in e for e in result["patch_errors"])


@pytest.mark.skipif(shutil.which("go") is None, reason="go toolchain not installed")
def test_revert_restores_pristine_state_for_multi_patch_same_file(temp_project):
    """Regression test: a real demo run sent two patches at the same file in
    one batch (one changing the signature, one updating the return inside
    the function). apply_fixes_node re-backs-up the file before applying
    each patch, so the second backup captures the file *after* the first
    patch already landed — not the pristine pre-batch content. When the
    build check then fails and triggers a revert, the file is restored to
    that post-first-patch snapshot instead of the original, leaving a
    half-patched, broken file on disk instead of a clean rollback.
    """
    (temp_project / "go.mod").write_text("module sample\n\ngo 1.21\n")
    target = temp_project / "readconfig.go"
    original = (
        "package sample\n\n"
        "func ReadConfig() []byte {\n"
        "\tdata := make([]byte, 1024)\n"
        "\treturn data\n"
        "}\n"
    )
    target.write_text(original)

    state = _state_with_patches(temp_project, [
        Patch(
            file_path=str(target),
            description="add error to signature",
            search_block="func ReadConfig() []byte {",
            replace_block="func ReadConfig() ([]byte, error) {",
        ),
        Patch(
            file_path=str(target),
            description="this patch fails to parse/apply, build stays broken",
            search_block="this text does not exist in the file",
            replace_block="irrelevant",
        ),
    ])

    result = apply_fixes_node(state)

    assert target.read_text() == original
    assert result["files_modified"] == []


@pytest.mark.skipif(
    shutil.which("gcc") is None and shutil.which("clang") is None,
    reason="no C compiler installed",
)
def test_reverts_patch_that_breaks_c_syntax(temp_project):
    target = temp_project / "main.c"
    target.write_text("int add(int a, int b) {\n    return a + b;\n}\n")

    state = _state_with_patches(temp_project, [
        Patch(
            file_path=str(target),
            description="break it",
            search_block="return a + b;",
            replace_block="return a + b",  # missing semicolon -> syntax error
        )
    ])

    result = apply_fixes_node(state)

    assert "return a + b;" in target.read_text()
    assert result["files_modified"] == []
    assert any("broke the build" in e for e in result["patch_errors"])


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_reverts_patch_that_breaks_js_syntax(temp_project):
    target = temp_project / "main.js"
    target.write_text("function add(a, b) {\n  return a + b;\n}\n")

    state = _state_with_patches(temp_project, [
        Patch(
            file_path=str(target),
            description="break it",
            search_block="return a + b;",
            replace_block="return a + b; }",  # extra brace -> syntax error
        )
    ])

    result = apply_fixes_node(state)

    assert target.read_text() == "function add(a, b) {\n  return a + b;\n}\n"
    assert result["files_modified"] == []
    assert any("broke the build" in e for e in result["patch_errors"])


def test_apply_fixes_logs_which_file_is_being_patched(temp_project, caplog):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")

    patch_obj = Patch(
        file_path=str(target), description="d", search_block="x = 1", replace_block="x = 2"
    )
    state = {"target_path": str(temp_project), "patches": [patch_obj], "patch_errors": []}

    caplog.set_level("INFO")
    apply_fixes_node(state)

    assert "main.py" in caplog.text
