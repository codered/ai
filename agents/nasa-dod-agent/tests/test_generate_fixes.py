from pathlib import Path
from unittest.mock import MagicMock, patch

from nasa_dod_agent.models import Finding, Patch, RubricConfig, Severity
from nasa_dod_agent.nodes.generate_fixes import _generate_patches, generate_fixes_node


def make_state(findings, fix_attempts=None):
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
        "fix_attempts": fix_attempts or {},
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
    """The prompt must show the LLM the actual current content of the
    finding's function, not just the finding's one-line description —
    otherwise the Search block it produces is a guess that won't reliably
    match the real text.
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
        function_name="Divide",
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
        function_name="Divide",
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


def test_generate_fixes_node_gives_up_after_max_attempts():
    """Regression test: a real run against a weak local model re-reviewed
    already-fixed files and kept reporting the same finding as still
    present, so the agent regenerated patches for it every iteration until
    max_iterations — burning the whole budget on one stuck finding instead
    of stopping and saying so. After max_fix_attempts_per_chunk failed
    attempts at the same (file, function, rule), the agent must stop
    trying and report why instead of spinning until max_iterations.
    """
    finding = _finding(Severity.P0)
    state = make_state([finding], fix_attempts={"a.py::None::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen:
        result = generate_fixes_node(state)

    mock_gen.assert_not_called()
    assert result["patches"] == []
    assert result["stop_reason"] == "max_fix_attempts"


def test_generate_fixes_node_increments_attempt_count():
    finding = _finding(Severity.P0)
    state = make_state([finding])

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    assert result["fix_attempts"] == {"a.py::None::R": 1}


def test_generate_fixes_node_only_sends_unexhausted_findings_to_llm():
    stuck = Finding(
        severity=Severity.P0, file_path="a.py", line_number=1, rule="R",
        description="D", why_fix="W",
    )
    fresh = Finding(
        severity=Severity.P0, file_path="b.py", line_number=1, rule="S",
        description="D2", why_fix="W2",
    )
    state = make_state([stuck, fresh], fix_attempts={"a.py::None::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert sent_findings == [fresh]
    assert result["fix_attempts"] == {"a.py::None::R": 2, "b.py::None::S": 1}


def test_finding_key_distinguishes_functions_in_same_file():
    """Two distinct functions with the same rule violation in the same
    file must be tracked (and capped) independently — sharing one retry
    budget across unrelated functions would let one stuck function's
    exhaustion block fixing an entirely different one."""
    from nasa_dod_agent.nodes.generate_fixes import _finding_key

    f1 = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D",
        why_fix="W", function_name="Foo",
    )
    f2 = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D",
        why_fix="W", function_name="Bar",
    )
    assert _finding_key(f1) != _finding_key(f2)


def test_generate_fixes_node_stops_at_max_total_fix_attempts():
    """Even if no single chunk has hit its own per-chunk cap, the run
    must stop once the sum of every attempt across every chunk reaches
    max_total_fix_attempts — otherwise a repo with many small findings
    could run an unbounded number of fix calls."""
    findings = [
        Finding(
            severity=Severity.P0, file_path=f"f{i}.py", rule="R",
            description="D", why_fix="W", function_name=f"fn{i}",
        )
        for i in range(3)
    ]
    config = RubricConfig(fix_threshold=1, max_total_fix_attempts=2)
    state = make_state(findings)
    state["config"] = config
    # Two attempts already used up by other findings earlier in the run.
    state["fix_attempts"] = {"other.py::None::X": 2}

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen:
        result = generate_fixes_node(state)

    mock_gen.assert_not_called()
    assert result["patches"] == []
    assert result["stop_reason"] == "max_total_fix_attempts"


def test_generate_fixes_node_trims_batch_to_remaining_total_budget():
    """If only partial budget remains, attempt as many findings as fit
    rather than refusing the whole batch outright."""
    findings = [
        Finding(
            severity=Severity.P0, file_path=f"f{i}.py", rule="R",
            description="D", why_fix="W", function_name=f"fn{i}",
        )
        for i in range(3)
    ]
    config = RubricConfig(fix_threshold=1, max_total_fix_attempts=5)
    state = make_state(findings)
    state["config"] = config
    state["fix_attempts"] = {"other.py::None::X": 4}  # 1 attempt of budget left

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert len(sent_findings) == 1
    assert sum(result["fix_attempts"].values()) == 5


def test_generate_fixes_node_skips_only_the_exhausted_function_in_a_shared_file():
    """Two functions in the SAME file, same rule: one has used up its
    per-chunk budget, the other hasn't. Only the exhausted one should be
    skipped — the sibling function must still get fixed normally."""
    exhausted = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D1",
        why_fix="W", function_name="Foo",
    )
    fresh = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D2",
        why_fix="W", function_name="Bar",
    )
    state = make_state([exhausted, fresh], fix_attempts={"a.go::Foo::R": 2})

    with patch("nasa_dod_agent.nodes.generate_fixes._generate_patches") as mock_gen, \
         patch("nasa_dod_agent.nodes.generate_fixes.LLMClient") as mock_llm:
        mock_gen.return_value = ([], [])
        mock_llm.from_env.return_value = MagicMock()
        result = generate_fixes_node(state)

    sent_findings = mock_gen.call_args[0][0]
    assert sent_findings == [fresh]
    assert result["fix_attempts"]["a.go::Foo::R"] == 2
    assert result["fix_attempts"]["a.go::Bar::R"] == 1


def test_chunk_text_for_finding_falls_back_to_whole_file_when_function_gone(temp_project):
    """A finding's function_name might no longer exist by the time a fix
    is attempted (e.g. a prior patch renamed/removed it) — the context
    builder must fall back to the whole file rather than erroring or
    silently showing nothing."""
    from nasa_dod_agent.nodes.generate_fixes import _chunk_text_for_finding

    target = temp_project / "divide.go"
    target.write_text("package sample\n\nfunc Divide(a, b int) int {\n\treturn a / b\n}\n")

    finding = Finding(
        severity=Severity.P0, file_path="divide.go", rule="R", description="D",
        why_fix="W", function_name="NoLongerExists",
    )

    text = _chunk_text_for_finding(finding, target)

    assert text == target.read_text()
