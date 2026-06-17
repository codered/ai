"""Assemble the LangGraph state machine for NASA/DOD review."""

from langgraph.graph import END, StateGraph

from nasa_dod_agent.checkpointer import FileSystemSaver
from nasa_dod_agent.nodes.apply_fixes import apply_fixes_node
from nasa_dod_agent.nodes.evaluate_rubric import evaluate_rubric_node
from nasa_dod_agent.nodes.generate_fixes import generate_fixes_node
from nasa_dod_agent.nodes.re_review_changed import re_review_changed_node
from nasa_dod_agent.nodes.review_code import review_code_node
from nasa_dod_agent.state import GraphState


def should_continue(state: GraphState) -> str:
    """Conditional edge: pass → END, fail → generate_fixes."""
    if state.get("rubric_passed", False):
        return "end"
    return "generate_fixes"


def build_graph(checkpoint_dir: str | None = None):
    """Build and compile the review agent graph."""
    workflow = StateGraph(GraphState)

    workflow.add_node("review_code", review_code_node)
    workflow.add_node("evaluate_rubric", evaluate_rubric_node)
    workflow.add_node("generate_fixes", generate_fixes_node)
    workflow.add_node("apply_fixes", apply_fixes_node)
    workflow.add_node("re_review_changed", re_review_changed_node)

    workflow.set_entry_point("review_code")

    workflow.add_edge("review_code", "evaluate_rubric")
    workflow.add_conditional_edges(
        "evaluate_rubric",
        should_continue,
        {"generate_fixes": "generate_fixes", "end": END},
    )
    workflow.add_edge("generate_fixes", "apply_fixes")
    workflow.add_edge("apply_fixes", "re_review_changed")
    workflow.add_edge("re_review_changed", "evaluate_rubric")

    checkpointer = None
    if checkpoint_dir:
        checkpointer = FileSystemSaver(checkpoint_dir)

    app = workflow.compile(checkpointer=checkpointer)
    return app
