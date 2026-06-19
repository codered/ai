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
