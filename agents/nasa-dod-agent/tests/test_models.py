from nasa_dod_agent.models import Finding, RubricConfig, Severity


def test_finding_creation():
    f = Finding(
        severity=Severity.P0,
        file_path="src/main.py",
        line_number=42,
        rule="NASA Power of Ten — Rule 2",
        description="Unbounded loop with no termination guarantee",
        why_fix="Can cause system hangs",
        fix_options=[],
    )
    assert f.severity == Severity.P0
    assert "unbounded" in f.description.lower()


def test_rubric_config_defaults():
    config = RubricConfig()
    assert config.max_p0 == 0
    assert config.max_p1 == 2
    assert config.fix_threshold == 1


def test_rubric_config_low_temperature_default():
    """Regression test: a real run showed the same file, reviewed twice at
    temperature=0.2, non-deterministically returning 2 findings one call
    and 0 the next. Default to 0 to minimize that sampling noise."""
    assert RubricConfig().temperature == 0.0


def test_rubric_config_review_samples_default():
    config = RubricConfig()
    assert config.review_samples == 1


def test_finding_function_name_defaults_to_none():
    f = Finding(
        severity=Severity.P0, file_path="a.go", rule="R", description="D", why_fix="W",
    )
    assert f.function_name is None


def test_rubric_config_max_iterations_lowered_to_five():
    """max_iterations dropped from 10 to 5 — with per-chunk reviewing now
    doing finer-grained work per iteration, fewer outer-loop iterations
    should be needed to converge."""
    assert RubricConfig().max_iterations == 5


def test_rubric_config_max_fix_attempts_per_chunk_default():
    assert RubricConfig().max_fix_attempts_per_chunk == 2


def test_rubric_config_max_total_fix_attempts_default():
    assert RubricConfig().max_total_fix_attempts == 20
