"""Node 5: re_review_changed — review only files modified in last apply."""

from pathlib import Path
from typing import List

from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding
from nasa_dod_agent.standards_loader import StandardsLoader
from nasa_dod_agent.state import GraphState


def _run_review(files: List[Path], llm_client: LLMClient, loader: StandardsLoader) -> List[Finding]:
    """Delegate to review_code's internal review function."""
    from nasa_dod_agent.nodes.review_code import _run_review as _original
    return _original(files, llm_client, loader)


def re_review_changed_node(state: GraphState) -> dict:
    """Review only files that were modified in the last apply."""
    files = [Path(f) for f in state.get("files_modified", []) if Path(f).exists()]

    if not files:
        return {"findings": state.get("findings", [])}

    llm = LLMClient.from_env(state["config"])
    loader = StandardsLoader()
    findings = _run_review(files, llm, loader)

    # Merge: keep findings from files that weren't re-reviewed
    reviewed_paths = {str(f) for f in files}
    old_findings = [f for f in state.get("findings", []) if f.file_path not in reviewed_paths]
    all_findings = old_findings + findings

    return {
        "findings": all_findings,
    }
