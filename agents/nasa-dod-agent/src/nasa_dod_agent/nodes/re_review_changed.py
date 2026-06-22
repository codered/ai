"""Node 5: re_review_changed — review only files modified in last apply."""

from pathlib import Path
from typing import List

from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding
from nasa_dod_agent.standards_loader import StandardsLoader
from nasa_dod_agent.state import GraphState


def _run_review(
    files: List[Path],
    llm_client: LLMClient,
    loader: StandardsLoader,
    base_path: Path,
    samples: int = 1,
) -> List[Finding]:
    """Delegate to review_code's internal review function."""
    from nasa_dod_agent.nodes.review_code import _run_review as _original
    return _original(files, llm_client, loader, base_path, samples=samples)


def re_review_changed_node(state: GraphState) -> dict:
    """Review only files that were modified in the last apply."""
    from nasa_dod_agent.nodes.review_code import _display_path

    base_path = Path(state["target_path"])
    files = [Path(f) for f in state.get("files_modified", []) if Path(f).exists()]

    if not files:
        return {"findings": state.get("findings", [])}

    config = state["config"]
    llm = LLMClient.from_env(config)
    loader = StandardsLoader()
    samples = config.review_samples if config else 1
    findings = _run_review(files, llm, loader, base_path, samples=samples)

    # Merge: keep findings from files that weren't re-reviewed. Findings store
    # file_path the same way review_code displayed it to the LLM, so reuse
    # that same helper to match them up.
    reviewed_paths = {_display_path(f, base_path) for f in files}
    old_findings = [f for f in state.get("findings", []) if f.file_path not in reviewed_paths]
    all_findings = old_findings + findings

    return {
        "findings": all_findings,
    }
