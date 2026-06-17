"""Node 3: generate_fixes — ask LLM to produce patches for fixable findings."""

from typing import List

from langchain_core.prompts import ChatPromptTemplate

from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding, Patch, Severity
from nasa_dod_agent.state import GraphState

SEVERITY_ORDER = {Severity.P0: 0, Severity.P1: 1, Severity.P2: 2, Severity.P3: 3}


def _should_fix(finding: Finding, threshold: int) -> bool:
    return SEVERITY_ORDER[finding.severity] <= threshold


def _generate_patches(findings: List[Finding], llm_client: LLMClient) -> List[Patch]:
    """Call LLM to generate patches for a batch of findings."""
    if not findings:
        return []

    findings_text = "\n\n".join(
        f"Finding: {f.description}\nFile: {f.file_path}\nLine: {f.line_number}\nRule: {f.rule}\nWhy: {f.why_fix}"
        for f in findings
    )

    system = (
        "You are a senior engineer. For each finding, produce a concrete code patch.\n\n"
        "Format each patch as:\n"
        "### Patch N: <brief title>\n"
        "**File:** `relative/path/to/file`\n"
        "**Description:** one sentence\n"
        "**Search:**\n```python\n<exact text to find>\n```\n"
        "**Replace:**\n```python\n<replacement text>\n```\n"
    )
    human = f"Findings to fix:\n\n{findings_text}"

    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    messages = prompt.format_messages()
    response = llm_client.get_llm().invoke(messages)

    parser = FixParser()
    patches, errors = parser.parse(response.content)
    return patches


def generate_fixes_node(state: GraphState) -> dict:
    """Generate patches for findings above the fix threshold."""
    threshold = state["config"].fix_threshold
    findings = [f for f in state.get("findings", []) if _should_fix(f, threshold)]

    if not findings:
        return {"patches": [], "patch_errors": []}

    llm = LLMClient.from_env(state["config"])
    patches = _generate_patches(findings, llm)

    return {
        "patches": patches,
        "patch_errors": [],
    }
