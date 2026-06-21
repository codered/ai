"""Node 1: review_code — perform NASA/DOD code review."""

import json
import logging
import re
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from nasa_dod_agent.chunker import FILE_LEVEL, chunk_file
from nasa_dod_agent.llm_client import LLMClient
from nasa_dod_agent.models import Finding, FixOption
from nasa_dod_agent.standards_loader import StandardsLoader
from nasa_dod_agent.state import GraphState

logger = logging.getLogger(__name__)


def _extract_findings(data: dict | list) -> list[dict]:
    """Pull findings from various LLM JSON wrapper shapes."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("findings", "data", "results", "items", "issues"):
            val = data.get(key)
            if isinstance(val, list):
                return val
        return [data] if data else []
    return []


def _normalise_fix_option(raw: dict) -> dict:
    """Map common LLM fix_option fields to FixOption model fields."""
    mapped = {}
    for k, v in raw.items():
        key = k.lower()
        if key in {"label", "description"}:
            mapped[key] = str(v)
        elif key == "code":
            mapped["code"] = str(v) if v is not None else None
        elif key == "recommended":
            mapped["recommended"] = bool(v)
        elif key in {"pros", "cons"}:
            if isinstance(v, str):
                mapped[key] = [v]
            elif isinstance(v, list):
                mapped[key] = [str(x) for x in v]
            else:
                mapped[key] = []
        elif key in FixOption.model_fields:
            mapped[key] = v
    return mapped


def _normalise_finding(raw: dict) -> dict:
    """Map common LLM field names to our model fields."""
    mapped = {}
    for k, v in raw.items():
        key = k.lower()
        if key in {"file", "filepath", "file_path", "filename"}:
            mapped["file_path"] = str(v)
        elif key in {"rule", "rule_id", "standard"}:
            mapped["rule"] = str(v)
        elif key == "severity":
            mapped["severity"] = str(v).upper()
        elif key in {"issue", "message", "description"}:
            mapped["description"] = str(v)
        elif key in {"why", "why_fix", "justification", "impact"}:
            mapped["why_fix"] = str(v)
        elif key == "line_number":
            mapped["line_number"] = int(v) if v is not None else None
        elif key == "fix_options" and isinstance(v, list):
            mapped["fix_options"] = [
                _normalise_fix_option(item) for item in v if isinstance(item, dict)
            ]
        elif key in Finding.model_fields:
            mapped[key] = v
    return mapped


def _strip_fences(content: str) -> str:
    """Strip markdown code fences so only raw JSON remains."""
    content = content.strip()
    # Remove opening fence (e.g. ```json or ``` followed by newline)
    if content.startswith("```"):
        newline_pos = content.find("\n")
        if newline_pos != -1:
            content = content[newline_pos + 1 :]
    # Remove closing fence
    if content.endswith("```"):
        last_newline = content.rfind("\n", 0, len(content) - 3)
        if last_newline != -1:
            content = content[:last_newline]
        else:
            content = content[: -len("```")]
    return content.strip()


def _parse_llm_response(content: str) -> list[Finding]:
    """Parse LLM output into Finding objects."""
    if not content or not content.strip():
        return []

    # Strategy 1: Strip fences and try direct JSON parse.
    stripped = _strip_fences(content)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        # Strategy 2: Bracket-matching for raw JSON arrays / objects.
        for candidate in _extract_json_brackets(content):
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            break
        else:
            data = None

    if data is None:
        import logging
        logging.getLogger(__name__).warning(
            "No JSON findings extracted from LLM response. First 200 chars: %r",
            content[:200],
        )
        return []

    raw_findings = _extract_findings(data)
    findings = _build_findings(raw_findings)
    if raw_findings and not findings:
        # raw_findings non-empty but nothing survived validation: the LLM
        # returned items that don't match our schema. An empty raw_findings
        # list just means the LLM found nothing wrong, which isn't a problem.
        import logging
        logging.getLogger(__name__).warning(
            "Parsed %d raw items but zero valid Findings.",
            len(raw_findings),
        )
    return findings


def _extract_json_brackets(text: str) -> list[str]:
    """Find top-level JSON arrays/objects by counting brackets/braces."""
    results: list[str] = []
    for m in re.finditer(r"[\[\{]", text):
        start = m.start()
        open_char = m.group()
        close_char = "]" if open_char == "[" else "}"
        depth = 1
        for i in range(start + 1, len(text)):
            char = text[i]
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        json.loads(candidate)
                        results.append(candidate)
                    except json.JSONDecodeError:
                        pass
                    break
    return results


def _build_findings(raw_findings: list[dict]) -> list[Finding]:
    """Convert raw dicts to validated Finding models."""
    findings: list[Finding] = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        normalised = _normalise_finding(item)
        allowed = set(Finding.model_fields.keys())
        filtered = {k: v for k, v in normalised.items() if k in allowed}
        try:
            findings.append(Finding(**filtered))
        except ValidationError:
            pass  # skip unparseable items
    return findings




# Extensions this agent knows how to review, mapped to the language name
# shown to the LLM in the system prompt.
EXTENSION_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".c": "c",
    ".h": "c",
    ".cpp": "c++",
    ".hpp": "c++",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
}


def _collect_files(
    target_path: str, mode: str, last_modified: List[str], target_file: str | None = None
) -> List[Path]:
    """Collect files to review based on mode.

    ``target_file``, when set, means the CLI was pointed at a single file
    rather than a directory — return just that file, ignoring mode and
    the exclude globs entirely.
    """
    if target_file:
        return [Path(target_file)]

    target = Path(target_path)
    if mode == "incremental" and last_modified:
        return [Path(f) for f in last_modified if Path(f).exists()]

    files = []
    for ext in EXTENSION_LANGUAGES:
        files.extend(target.rglob(f"*{ext}"))
    # Exclude common non-source
    exclude = {"node_modules", ".git", "venv", "__pycache__", ".nasa-dod-agent"}
    return [f for f in files if not any(part in exclude for part in f.parts)]


def _detect_languages(files: List[Path]) -> List[str]:
    """Languages actually present among the files being reviewed.

    The system prompt reports this to the LLM, so it must reflect the real
    target — telling a reviewer "Languages detected: python" while showing
    it Go code is misleading and undermines the review.
    """
    languages = {
        EXTENSION_LANGUAGES.get(f.suffix, f.suffix.lstrip(".") or "unknown") for f in files
    }
    return sorted(languages)


def _display_path(f: Path, base_path: Path) -> str:
    """Path to show the LLM: relative to the project root when possible.

    Findings/patches carry this string as ``file_path`` and it must be
    resolvable later (in ``apply_fixes_node``) relative to the project
    root, so a bare filename isn't enough once subdirectories are involved.
    """
    try:
        return str(f.relative_to(base_path))
    except ValueError:
        return str(f)


def _dedupe_findings(findings: List[Finding]) -> List[Finding]:
    """Keep one Finding per (file_path, rule), first-seen wins.

    Multiple review samples of the same file legitimately report the same
    real finding more than once — that must count once, not N times.
    """
    seen: dict[tuple[str, str], Finding] = {}
    for f in findings:
        key = (f.file_path, f.rule)
        if key not in seen:
            seen[key] = f
    return list(seen.values())


def _run_review(
    files: List[Path],
    llm_client: LLMClient,
    loader: StandardsLoader,
    base_path: Path,
    samples: int = 1,
) -> List[Finding]:
    """Call LLM to review the collected files, one function/chunk per call.

    Each file is split into chunks (one per top-level function/method,
    plus a file-level chunk for everything else) via ``chunk_file`` — a
    real run showed that batching even two small, unrelated files into
    one prompt made the model report zero findings, even though it
    reliably caught the exact same issue when shown the offending content
    alone. Reviewing one chunk per call costs more calls but avoids that
    dilution.

    ``samples`` reviews each chunk that many times and unions the results
    (deduped per chunk) — a real run showed the same content, same
    prompt, returning findings on one call and none on the next at
    temperature 0.2, so a single sample isn't reliable evidence of a
    clean chunk on a noisy model.
    """
    findings: List[Finding] = []
    for f in files:
        display_path = _display_path(f, base_path)
        language = EXTENSION_LANGUAGES.get(f.suffix, "")
        chunks = chunk_file(f, language)

        function_count = sum(1 for c in chunks if c.name != FILE_LEVEL)
        noun = "function" if function_count == 1 else "functions"
        logger.info("Reviewing %s (%d %s)", display_path, function_count, noun)

        for chunk in chunks:
            logger.info("  └─ %s", chunk.name)
            label = "file-level code" if chunk.name == FILE_LEVEL else f"function {chunk.name}"
            system_prompt = loader.build_system_prompt(languages=_detect_languages([f]))
            human_prompt = f"Review the following {label} from {display_path}:\n\n{chunk.text}"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
            chunk_findings: List[Finding] = []
            for _ in range(samples):
                raw = llm_client.get_llm().invoke(messages)
                chunk_findings.extend(_parse_llm_response(str(raw.content)))

            for finding in chunk_findings:
                finding.function_name = None if chunk.name == FILE_LEVEL else chunk.name
                if finding.line_number is not None:
                    finding.line_number += chunk.start_line - 1

            findings.extend(_dedupe_findings(chunk_findings))

    return findings




def review_code_node(state: GraphState) -> dict:
    """Review code and return findings."""
    files = _collect_files(
        state["target_path"],
        state["review_mode"],
        state.get("last_modified_files", []),
        target_file=state.get("target_file"),
    )

    if not files:
        return {"findings": [], "files_reviewed": state.get("files_reviewed", [])}

    llm = LLMClient.from_env(state["config"])
    loader = StandardsLoader()
    samples = state["config"].review_samples
    findings = _run_review(files, llm, loader, Path(state["target_path"]), samples=samples)

    files_reviewed = list(set(state.get("files_reviewed", []) + [str(f) for f in files]))

    return {
        "findings": findings,
        "files_reviewed": files_reviewed,
    }
