"""Node 3: generate_fixes — ask LLM to produce patches for fixable findings."""

import logging
from pathlib import Path
from typing import List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file
from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding, Patch, PatchError, Severity
from nasa_dod_agent.nodes.review_code import EXTENSION_LANGUAGES
from nasa_dod_agent.state import GraphState

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {Severity.P0: 0, Severity.P1: 1, Severity.P2: 2, Severity.P3: 3}


def _should_fix(finding: Finding, threshold: int) -> bool:
    return SEVERITY_ORDER[finding.severity] <= threshold


def _finding_key(finding: Finding) -> str:
    return f"{finding.file_path}::{finding.function_name}::{finding.rule}"


def _resolve(file_path: str, target_path: Path) -> Path:
    p = Path(file_path)
    return p if p.is_absolute() else target_path / p


def _chunk_text_for_finding(finding: Finding, path: Path) -> str:
    """The exact text of the function (or file-level code) a finding
    belongs to. Falls back to the whole file if the chunk no longer
    exists — e.g. a prior patch renamed/removed the function."""
    language = EXTENSION_LANGUAGES.get(path.suffix, "")
    chunks = chunk_file(path, language)
    target_name = finding.function_name or FILE_LEVEL
    for chunk in chunks:
        if chunk.name == target_name:
            return chunk.text
    return path.read_text()


def _file_contents_context(findings: List[Finding], target_path: Path) -> str:
    """Show the LLM the real, current content of each finding's function
    (or file-level code), not the finding's one-line description — which
    routinely doesn't match exact source text and gives no way to know
    what's already imported or already there.
    """
    context = ""
    seen = set()
    for f in findings:
        key = (f.file_path, f.function_name)
        if key in seen:
            continue
        seen.add(key)
        path = _resolve(f.file_path, target_path)
        if not path.exists():
            continue
        chunk_text = _chunk_text_for_finding(f, path)
        label = f.file_path if f.function_name is None else f"{f.file_path}::{f.function_name}"
        context += f"\n--- {label} ---\n{chunk_text}\n"
    return context


def _generate_patches(
    findings: List[Finding],
    llm_client: LLMClient,
    target_path: Path,
    previous_errors: List[str] | None = None,
) -> Tuple[List[Patch], List[PatchError]]:
    """Call LLM to generate patches for a batch of findings."""
    if not findings:
        return [], []

    findings_text = "\n\n".join(
        f"Finding: {f.description}\n"
        f"File: {f.file_path}\n"
        f"Line: {f.line_number}\n"
        f"Rule: {f.rule}\n"
        f"Why: {f.why_fix}"
        for f in findings
    )
    file_context = _file_contents_context(findings, target_path)

    system = (
        "You are a senior engineer. For each finding, produce a concrete code patch.\n\n"
        "Make the SMALLEST change that resolves the specific finding — nothing else. "
        "Do not change a function's signature, parameter types, or name unless the "
        "finding is literally about that signature. Do not add new dependencies, "
        "concurrency primitives, configurability, or 'production-ready' scaffolding "
        "the finding didn't ask for. Do not leave TODO-style comments or placeholder "
        "logic (e.g. 'should use a proper logger in production') — either implement it "
        "or leave it out. A bigger, cleverer rewrite is a worse patch than a small, "
        "boring one: every extra change you make is new surface area for the next "
        "review pass to flag.\n\n"
        "The Search block MUST be copied verbatim from the file contents shown below — "
        "not reconstructed from memory or the finding's description. If you can't find "
        "exact text to match, say so in the Description instead of guessing.\n\n"
        "The Search block must also be unique: it has to match exactly one location in "
        "the file. If the lines you want to change also appear elsewhere in the file "
        "(e.g. a repeated `if err != nil { ... }` idiom), they are not enough on their "
        "own — include an extra line of surrounding context (the line just before or "
        "after) that differs between the locations, so the block matches only the one "
        "you intend to change.\n\n"
        "If fixing a finding requires changing more than one location in a file (for "
        "example, adding an import AND changing a function body), emit a SEPARATE "
        "### Patch entry for each location — one Search/Replace pair per location.\n\n"
        "Format each patch as:\n"
        "### Patch N: <brief title>\n"
        "**File:** `relative/path/to/file`\n"
        "**Description:** one sentence\n"
        "**Search:**\n```\n<exact text to find>\n```\n"
        "**Replace:**\n```\n<replacement text>\n```\n"
    )
    human = (
        f"Findings to fix:\n\n{findings_text}\n\n"
        f"Current file contents:\n{file_context}"
    )
    if previous_errors:
        errors_text = "\n".join(f"- {e}" for e in previous_errors)
        human += (
            "\n\nA previous attempt at fixing these same findings caused the following "
            "problems — the file contents above are already back to their original state "
            "(those attempts were reverted), but make sure your new patches don't repeat "
            f"the same mistake:\n{errors_text}"
        )

    messages = [SystemMessage(content=system), HumanMessage(content=human)]
    response = llm_client.get_llm().invoke(messages)

    parser = FixParser()
    return parser.parse(response.content)


def generate_fixes_node(state: GraphState) -> dict:
    """Generate patches for findings above the fix threshold, bounded by
    a per-chunk retry cap and a global total-attempts cap."""
    config = state["config"]
    threshold = config.fix_threshold
    fixable = [f for f in state.get("findings", []) if _should_fix(f, threshold)]

    if not fixable:
        # Nothing left to fix at this threshold, but the rubric is still
        # failing (that's the only way we'd get here) — looping further
        # would never change anything, so say so and stop.
        return {"patches": [], "patch_errors": [], "stop_reason": "no_fixable_findings"}

    fix_attempts = dict(state.get("fix_attempts", {}))
    per_chunk_cap = config.max_fix_attempts_per_chunk
    findings = [f for f in fixable if fix_attempts.get(_finding_key(f), 0) < per_chunk_cap]

    if not findings:
        # Every fixable finding has already been retried past its own
        # cap — the model isn't converging on these, so stop instead of
        # spinning through the rest of max_iterations on findings that
        # won't budge.
        return {"patches": [], "patch_errors": [], "stop_reason": "max_fix_attempts"}

    total_attempts_so_far = sum(fix_attempts.values())
    remaining_budget = config.max_total_fix_attempts - total_attempts_so_far
    if remaining_budget <= 0:
        # The whole run has already spent its total fix-attempt budget,
        # even though no single chunk hit its own per-chunk cap — likely
        # many small findings adding up. Stop rather than keep going.
        return {"patches": [], "patch_errors": [], "stop_reason": "max_total_fix_attempts"}
    findings.sort(key=lambda f: SEVERITY_ORDER[f.severity])
    if len(findings) > remaining_budget:
        findings = findings[:remaining_budget]

    for f in findings:
        key = _finding_key(f)
        fix_attempts[key] = fix_attempts.get(key, 0) + 1
        logger.info(
            "Fixing %s::%s (%s: %s)",
            f.file_path, f.function_name or FILE_LEVEL, f.severity.value, f.description,
        )

    llm = LLMClient.from_env(config)
    target_path = Path(state["target_path"])
    previous_errors = state.get("patch_errors", [])
    patches, parse_errors = _generate_patches(findings, llm, target_path, previous_errors)

    return {
        "patches": patches,
        "patch_errors": [f"{e.file_path}: {e.error_message}" for e in parse_errors],
        "fix_attempts": fix_attempts,
    }
