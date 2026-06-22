from pathlib import Path
from unittest.mock import MagicMock, patch

from nasa_dod_agent.chunker import FILE_LEVEL
from nasa_dod_agent.models import Finding, Severity
from nasa_dod_agent.nodes.review_code import _collect_files, _detect_languages, _run_review, review_code_node
from nasa_dod_agent.standards_loader import StandardsLoader
from nasa_dod_agent.state import GraphState


def test_detect_languages_matches_file_extensions():
    """Regression test: the system prompt once always said 'python' even
    when reviewing Go (or any other) code, which misled the LLM."""
    assert _detect_languages([Path("iseven.go"), Path("test/iseven_test.go")]) == ["go"]
    assert _detect_languages([Path("a.py"), Path("b.rs")]) == ["python", "rust"]
    assert _detect_languages([]) == []


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
        patch("nasa_dod_agent.nodes.review_code.LLMClient"),
    ):
        mock_review.return_value = [mock_finding]
        result = review_code_node(state)

    assert len(result["findings"]) == 1
    assert result["findings"][0].severity == Severity.P0
    assert any("main.py" in f for f in result["files_reviewed"])


def test_run_review_sends_full_file_content_past_2000_chars(temp_project):
    """Regression test: a real run against a 3300-byte test file found zero
    issues even though the file had a duplicate function declaration (a Go
    vet/build error) past the 2000-char mark — because _run_review sliced
    file content to f.read_text()[:2000] before sending it to the LLM, so
    the duplicate was silently never shown to the model at all.
    """
    target = temp_project / "big.go"
    filler = "// padding line to push past the old 2000-char cutoff\n" * 60
    marker = "func DuplicateMarker() {}\n"
    target.write_text(filler + marker)
    assert len(filler) > 2000

    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = "[]"

    _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    all_calls = mock_llm_client.get_llm.return_value.invoke.call_args_list
    human_contents = [call.args[0][1].content for call in all_calls]
    assert any(marker.rstrip("\n") in content for content in human_contents)


def test_run_review_calls_llm_once_per_file(temp_project):
    """Regression test: a real run batched two unrelated files into one
    review prompt and the model returned zero findings, even though it
    reliably caught the same issue when shown the offending file alone.
    Reviewing one file per LLM call avoids that cross-file dilution.
    """
    file_a = temp_project / "a.go"
    file_a.write_text("package a\n")
    file_b = temp_project / "b.go"
    file_b.write_text("package b\n")

    # Both files have no functions, so chunk_file gives each a single
    # "<file-level>" chunk (len(chunks) == 1) — the whole-file pass is
    # skipped for single-chunk files (Finding 2), so each file gets exactly
    # one per-chunk call: two files = 2 total calls.
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(
            content='[{"severity": "P2", "file_path": "a.go", "rule": "R", '
            '"description": "D", "why_fix": "W"}]'
        ),
        MagicMock(content="[]"),  # b.go per-chunk
    ]

    findings = _run_review(
        [file_a, file_b], mock_llm_client, StandardsLoader(), temp_project
    )

    assert mock_llm_client.get_llm.return_value.invoke.call_count == 2
    assert len(findings) == 1
    assert findings[0].file_path == "a.go"


def test_run_review_samples_each_file_n_times(temp_project):
    """Regression test: the same file reviewed twice at temperature=0.2
    returned 2 findings on one call and 0 on the next — pure LLM sampling
    noise on identical input. Sampling each file N times and unioning
    findings means a finding only needs to surface on ONE of N attempts.
    """
    target = temp_project / "a.go"
    target.write_text("package a\n")

    # "package a\n" has no functions, so chunk_file gives a single
    # "<file-level>" chunk (len(chunks) == 1) — the whole-file pass is
    # skipped for single-chunk files (Finding 2). samples=3 means 3
    # per-chunk calls only = 3 total.
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(content="[]"),
        MagicMock(
            content='[{"severity": "P2", "file_path": "a.go", "rule": "R", '
            '"description": "D", "why_fix": "W"}]'
        ),
        MagicMock(content="[]"),
    ]

    findings = _run_review(
        [target], mock_llm_client, StandardsLoader(), temp_project, samples=3
    )

    assert mock_llm_client.get_llm.return_value.invoke.call_count == 3
    assert len(findings) == 1
    assert findings[0].rule == "R"


def test_run_review_dedupes_same_finding_across_samples(temp_project):
    """A finding reported by more than one sample for the same file must
    count once, not N times — otherwise severity counts and fix-attempt
    tracking would be inflated by how many samples happened to agree.
    """
    target = temp_project / "a.go"
    target.write_text("package a\n")

    same_finding_json = (
        '[{"severity": "P0", "file_path": "a.go", "rule": "R", '
        '"description": "D", "why_fix": "W"}]'
    )
    # "package a\n" has no functions, so chunk_file gives a single
    # "<file-level>" chunk (len(chunks) == 1) — the whole-file pass is
    # skipped for single-chunk files (Finding 2). samples=2 means 2
    # per-chunk calls only, both returning the same finding, which the
    # per-chunk dedupe must collapse to one.
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(content=same_finding_json),
        MagicMock(content=same_finding_json),
    ]

    findings = _run_review(
        [target], mock_llm_client, StandardsLoader(), temp_project, samples=2
    )

    assert len(findings) == 1


def test_collect_files_returns_only_target_file_when_set(temp_project):
    (temp_project / "a.go").write_text("package a\n")
    (temp_project / "b.go").write_text("package b\n")
    target_file = str(temp_project / "a.go")

    files = _collect_files(str(temp_project), "full", [], target_file=target_file)

    assert files == [Path(target_file)]


def test_collect_files_globs_normally_when_no_target_file(temp_project):
    (temp_project / "a.go").write_text("package a\n")

    files = _collect_files(str(temp_project), "full", [], target_file=None)

    assert files == [temp_project / "a.go"]


def test_run_review_stamps_function_name_and_offsets_line_number(temp_project):
    target = temp_project / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "func Foo() {\n"
        "\tx := 1\n"
        "}\n"
    )

    # Real chunk_file on this source produces TWO chunks — the "Foo" function
    # (lines 3-5) and a "<file-level>" chunk for the "package sample\n\n"
    # preamble — so the mock needs one response per chunk, in chunk_file's
    # order (function chunks first, file-level last), rather than one
    # blanket `.return_value` for every call.
    # Two per-chunk calls (Foo, then file-level) plus one whole-file pass
    # call (samples=1 default) = 3 total. The whole-file pass returns "[]"
    # so it doesn't add a second finding to this test's assertions.
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(content=(
            '[{"severity": "P2", "file_path": "sample.go", "rule": "R", '
            '"description": "D", "why_fix": "W", "line_number": 2}]'
        )),
        MagicMock(content="[]"),
        MagicMock(content="[]"),
    ]

    findings = _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert len(findings) == 1
    assert findings[0].function_name == "Foo"
    assert findings[0].line_number == 4


def test_run_review_includes_whole_file_pass_for_cross_function_issues(temp_project):
    """Per-function chunking reviews each function in total isolation, so
    it cannot notice that two DIFFERENT functions share the same name (a
    real Go vet "redeclared" error) — that fact only exists at the
    whole-file level. A real run confirmed this: chunking correctly
    produced two separate chunks for two identically-named functions, but
    neither chunk's review could flag the collision. A supplemental
    whole-file pass after the per-chunk calls restores that visibility.
    """
    target = temp_project / "dup.go"
    target.write_text(
        "package sample\n"
        "\n"
        "func TestIsEven_maxUint() {}\n"
        "\n"
        "func TestIsEven_maxUint() {}\n"
    )

    mock_llm_client = MagicMock()
    # Two function chunks + one file-level chunk (the "package sample\n\n"
    # preamble) = 3 per-chunk calls, then one whole-file pass call = 4
    # total. Only the LAST call (the whole-file pass) returns a finding.
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(content="[]"),
        MagicMock(content="[]"),
        MagicMock(content="[]"),
        MagicMock(content=(
            '[{"severity": "P0", "file_path": "dup.go", "rule": "R", '
            '"description": "TestIsEven_maxUint declared twice", '
            '"why_fix": "W"}]'
        )),
    ]

    findings = _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert mock_llm_client.get_llm.return_value.invoke.call_count == 4
    assert len(findings) == 1
    assert findings[0].function_name is None
    assert "declared twice" in findings[0].description


def test_run_review_whole_file_pass_does_not_duplicate_chunk_finding(temp_project):
    """Finding 1 regression test: nothing stops the whole-file pass from
    re-reporting an issue a per-chunk call already found for the same
    file. When that happens, the SAME real issue would otherwise be
    counted twice — once correctly attributed to "Foo" (the chunk pass)
    and once with function_name forced to None (the whole-file pass) —
    inflating severity counts and causing generate_fixes to attempt two
    separate patches for one real issue. The fix filters whole-file-pass
    findings against the set of rules already found by THIS FILE's own
    chunks, dropping the redundant repeat.
    """
    target = temp_project / "sample.go"
    target.write_text(
        "package sample\n"
        "\n"
        "func Foo() {\n"
        "\tx := 1\n"
        "}\n"
    )

    # chunk_file gives TWO chunks for this source ("Foo", then
    # "<file-level>"), so len(chunks) > 1 and the whole-file pass runs:
    # two per-chunk calls + one whole-file pass call = 3 total. The chunk
    # call for "Foo" reports rule "R"; the whole-file pass ALSO reports
    # rule "R" (simulating the model re-reporting the same real issue at
    # the whole-file level) — that repeat must be dropped.
    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.side_effect = [
        MagicMock(content=(
            '[{"severity": "P2", "file_path": "sample.go", "rule": "R", '
            '"description": "Foo issue", "why_fix": "W"}]'
        )),
        MagicMock(content="[]"),  # file-level chunk: clean
        MagicMock(content=(
            '[{"severity": "P2", "file_path": "sample.go", "rule": "R", '
            '"description": "Foo issue restated at whole-file level", '
            '"why_fix": "W"}]'
        )),
    ]

    findings = _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    matching = [fnd for fnd in findings if fnd.rule == "R"]
    assert len(matching) == 1
    assert matching[0].function_name == "Foo"


def test_run_review_skips_whole_file_pass_for_single_chunk_file(temp_project):
    """Finding 2 regression test: a file with zero functions chunks down
    to a single "<file-level>" fallback chunk. A second whole-file-style
    pass over that exact same content would just review identical text
    twice for nothing, so it must be skipped entirely when
    len(chunks) <= 1 — exactly one LLM call total, not two.
    """
    target = temp_project / "nofuncs.go"
    target.write_text("package nofuncs\n\nvar X = 1\n")

    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = "[]"

    _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert mock_llm_client.get_llm.return_value.invoke.call_count == 1


def test_run_review_logs_file_and_function_progress(temp_project, caplog):
    target = temp_project / "sample.go"
    target.write_text("package sample\n\nfunc Foo() {}\n")

    mock_llm_client = MagicMock()
    mock_llm_client.get_llm.return_value.invoke.return_value.content = "[]"

    caplog.set_level("INFO")
    _run_review([target], mock_llm_client, StandardsLoader(), temp_project)

    assert "Reviewing sample.go (1 function)" in caplog.text
    assert "Foo" in caplog.text
