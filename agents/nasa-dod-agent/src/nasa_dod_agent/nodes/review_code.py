"""Node 1: review_code — perform NASA/DOD code review."""

import json
from pathlib import Path
from typing import List

from langchain_core.prompts import ChatPromptTemplate

from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding
from nasa_dod_agent.standards_loader import StandardsLoader
from nasa_dod_agent.state import GraphState


def _collect_files(target_path: str, mode: str, last_modified: List[str]) -> List[Path]:
    """Collect files to review based on mode."""
    target = Path(target_path)
    if mode == "incremental" and last_modified:
        return [Path(f) for f in last_modified if Path(f).exists()]

    # Full mode: all Python, JS, TS, C, C++, Go, Rust, Java files
    extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".c", ".cpp", ".h", ".hpp",
        ".go", ".rs", ".java",
    }
    files = []
    for ext in extensions:
        files.extend(target.rglob(f"*{ext}"))
    # Exclude common non-source
    exclude = {"node_modules", ".git", "venv", "__pycache__", ".nasa-dod-agent"}
    return [f for f in files if not any(part in exclude for part in f.parts)]


def _run_review(files: List[Path], llm_client: LLMClient, loader: StandardsLoader) -> List[Finding]:
    """Call LLM to review the collected files."""
    if not files:
        return []

    # Build context: file paths + small content summaries
    file_context = ""
    for f in files:
        content = f.read_text()[:2000]  # first 2000 chars per file
        file_context += f"\n--- {f.name} ---\n{content}\n"

    system_prompt = loader.build_system_prompt(languages=["python"])
    human_prompt = f"Review the following files:\n{file_context}"

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", human_prompt)]
    )

    messages = prompt.format_messages()
    raw = llm_client.get_llm().invoke(messages)

    # Try to parse as JSON array of findings
    try:
        data = json.loads(raw.content)
        if isinstance(data, list):
            return [Finding(**item) for item in data]
        elif isinstance(data, dict):
            return [Finding(**data)]
    except (json.JSONDecodeError, TypeError):
        pass

    return []


def review_code_node(state: GraphState) -> dict:
    """Review code and return findings."""
    files = _collect_files(
        state["target_path"],
        state["review_mode"],
        state.get("last_modified_files", []),
    )

    if not files:
        return {"findings": [], "files_reviewed": state.get("files_reviewed", [])}

    llm = LLMClient.from_env(state["config"])
    loader = StandardsLoader()
    findings = _run_review(files, llm, loader)

    files_reviewed = list(set(state.get("files_reviewed", []) + [str(f) for f in files]))

    return {
        "findings": findings,
        "files_reviewed": files_reviewed,
    }
