from pathlib import Path
from unittest.mock import MagicMock, patch

from nasa_dod_agent.models import Finding, Patch, RubricConfig, Severity
from nasa_dod_agent.nodes.generate_fixes import _generate_patches, generate_fixes_node


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

def _finding(severity):
    return Finding(
        severity=severity, file_path="a.py", line_number=1, rule="R", description="D", why_fix="W"
    )


def test_generates_patches_for_fixable_findings():
    state = make_state([_finding(Severity.P1)])

    mock_patch = Patch(file_path="a.py", description="fix", search_block="x", replace_block="y")
    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([mock_patch], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    assert len(result["patches"]) == 1
    assert result["patches"][0].file_path == "a.py"

def test_no_fixes_for_p3_only():
    state = make_state([_finding(Severity.P3)])
    result = generate_fixes_node(state)
    assert result["patches"] == []
    assert result["stop_reason"] == "no_fixable_findings"


def test_generate_patches_handles_braces_in_finding_text():
    """Regression test: a finding describing brace-using code (e.g. Go's
    `for { ... }`) once crashed _generate_patches because it built the
    prompt with ChatPromptTemplate, which parses '{...}' as an f-string
    template variable instead of literal text.
    """
    finding = Finding(
        severity=Severity.P0,
        file_path="loop.go",
        line_number=5,
        rule="NASA Rule 2",
        description="Unbounded loop: for { ... } never terminates",
        why_fix="A bare for { } loop with no break condition can hang the process.",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    patches, errors = _generate_patches([finding], mock_llm_client, Path("."))

    assert patches == []
    assert errors == []
    mock_llm_client.get_llm.return_value.invoke.assert_called_once()


def test_generate_patches_includes_real_file_content(temp_project):
    """The prompt must show the LLM the actual current file content, not
    just the finding's one-line description — otherwise the Search block
    it produces is a guess that won't reliably match the real text.
    """
    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0,
        file_path="divide.go",
        line_number=4,
        rule="NASA Rule",
        description="No zero-divisor check",
        why_fix="Panics at runtime on b == 0",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    _generate_patches([finding], mock_llm_client, temp_project)

    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    human_content = sent_messages[1].content
    assert "func Divide(a, b int) int {" in human_content
    assert "return a / b" in human_content


def test_generate_patches_feeds_back_previous_failure(temp_project):
    """Regression test: a real run kept regenerating the exact same broken
    patch (missing 'import errors') every iteration for 10 iterations,
    because the agent never told the LLM its previous attempt had been
    reverted for a specific reason. The previous patch_errors must reach
    the prompt so the model can avoid repeating the mistake.
    """
    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0,
        file_path="divide.go",
        line_number=4,
        rule="NASA Rule",
        description="No zero-divisor check",
        why_fix="Panics at runtime on b == 0",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    previous_errors = [
        "Reverted 1 file(s) — patches broke the build: `go build ./...` failed:\n"
        "./divide.go:10:13: undefined: errors"
    ]
    _generate_patches([finding], mock_llm_client, temp_project, previous_errors)

    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    human_content = sent_messages[1].content
    assert "undefined: errors" in human_content
    assert "previous attempt" in human_content


def test_generate_patches_prompt_requires_unique_search_block():
    """Regression test: a real run got stuck for 10 iterations because the
    LLM kept producing a Search block that matched two identical
    `if err != nil { return nil }` blocks in the same file (readconfig.go),
    and the system prompt never told it the Search block must be unique —
    it only said to copy text verbatim, not that the copied text also has
    to disambiguate itself from other occurrences.
    """
    finding = Finding(
        severity=Severity.P0, file_path="a.go", line_number=1, rule="R",
        description="D", why_fix="W",
    )
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = ""

    _generate_patches([finding], mock_llm_client, Path("."))

    sent_messages = mock_llm_client.get_llm.return_value.invoke.call_args[0][0]
    system_content = sent_messages[0].content
    assert "unique" in system_content.lower()


def test_generate_fixes_node_passes_patch_errors_as_feedback():
    """generate_fixes_node must forward state['patch_errors'] from the
    prior iteration into _generate_patches, not just the findings.
    """
    state = make_state([_finding(Severity.P0)])
    state["patch_errors"] = ["divide.go: undefined: errors"]

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        generate_fixes_node(state)

    args, _ = mock_gen.call_args
    assert args[3] == ["divide.go: undefined: errors"]
