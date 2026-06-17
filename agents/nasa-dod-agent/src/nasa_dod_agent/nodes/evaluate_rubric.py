"""Node 2: evaluate_rubric — count severities and decide if threshold met."""

from nasa_dod_agent.models import Severity
from nasa_dod_agent.state import GraphState


def evaluate_rubric_node(state: GraphState) -> dict:
    """Count findings by severity and compare to config thresholds."""
    config = state["config"]
    findings = state.get("findings", [])

    counts = {Severity.P0: 0, Severity.P1: 0, Severity.P2: 0, Severity.P3: 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    rubric_passed = (
        counts[Severity.P0] <= config.max_p0
        and counts[Severity.P1] <= config.max_p1
        and counts[Severity.P2] <= config.max_p2
        and counts[Severity.P3] <= config.max_p3
    )

    iteration = state["iteration"] + 1
    maxed_out = iteration >= config.max_iterations
    if maxed_out and not rubric_passed:
        rubric_passed = True

    return {
        "rubric_passed": rubric_passed,
        "p0_count": counts[Severity.P0],
        "p1_count": counts[Severity.P1],
        "p2_count": counts[Severity.P2],
        "p3_count": counts[Severity.P3],
        "iteration": iteration,
    }
