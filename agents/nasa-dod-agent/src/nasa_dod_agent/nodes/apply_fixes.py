"""Node 4: apply_fixes — atomically apply patches to disk with backups."""

import shutil
import subprocess
import sys
from pathlib import Path

from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.state import GraphState

_BUILD_TIMEOUT_SECONDS = 60


def _run_checker(cmd: list[str], cwd: Path | None = None) -> str | None:
    """Run one syntax/build-check command.

    Returns an error message if it failed, or None if it passed — or if it
    timed out, since a slow check isn't proof the patch broke anything.
    """
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=_BUILD_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode == 0:
        return None
    output = (result.stderr or result.stdout).strip()
    return f"`{' '.join(cmd)}` failed:\n{output[:500]}"


def _first_available(*names: str) -> str | None:
    """First of these command names that's actually installed, if any."""
    for name in names:
        if shutil.which(name):
            return name
    return None


def _verify_build(target_path: Path, modified_files: list[str]) -> str | None:
    """Best-effort: run the right toolchain for each touched language to
    check the patches didn't leave a file internally inconsistent (e.g. a
    return type was changed but not every return statement, or a needed
    import wasn't added). FixParser already rejects corrupted/truncated
    text edits; this catches the case where the edit is individually
    well-formed but the file as a whole no longer builds.

    Each check is skipped silently if its tool isn't installed — this is a
    bonus safety net, not a hard requirement, so an unsupported language or
    missing compiler just means "no extra check," not a failure.
    """
    py_files = [f for f in modified_files if f.endswith(".py")]
    if py_files:
        error = _run_checker([sys.executable, "-m", "py_compile", *py_files])
        if error:
            return error

    if any(f.endswith(".go") for f in modified_files) and shutil.which("go"):
        error = _run_checker(["go", "build", "./..."], cwd=target_path)
        if error:
            return error

    c_files = [f for f in modified_files if f.endswith(".c")]
    cc = _first_available("gcc", "clang", "cc")
    if c_files and cc:
        for f in c_files:
            error = _run_checker([cc, "-fsyntax-only", f])
            if error:
                return error

    cpp_files = [f for f in modified_files if f.endswith(".cpp")]
    cxx = _first_available("g++", "clang++", "c++")
    if cpp_files and cxx:
        for f in cpp_files:
            error = _run_checker([cxx, "-fsyntax-only", "-std=c++17", f])
            if error:
                return error

    js_files = [f for f in modified_files if f.endswith(".js")]
    if js_files and shutil.which("node"):
        for f in js_files:
            error = _run_checker(["node", "--check", f])
            if error:
                return error

    return None


def apply_fixes_node(state: GraphState) -> dict:
    """Apply patches to disk, creating backups in .nasa-dod-agent/backups/."""
    patches = state.get("patches", [])
    if not patches:
        return {
            "files_modified": [],
            "backup_paths": [],
            "patch_errors": [],
            "last_modified_files": [],
        }

    target_path = Path(state["target_path"])
    backup_dir = target_path / ".nasa-dod-agent" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    parser = FixParser()
    files_modified = []
    backup_paths = []
    backup_for: dict[str, Path] = {}
    errors = []

    for patch in patches:
        try:
            file_path = Path(patch.file_path)
            if not file_path.is_absolute():
                file_path = target_path / file_path
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                continue

            # Create backup in .nasa-dod-agent/backups/
            local_backup = backup_dir / (file_path.name + ".bak")
            local_backup.write_bytes(file_path.read_bytes())

            parser.apply_patch(patch, file_path)

            files_modified.append(str(file_path))
            backup_paths.append(str(local_backup))
            backup_for[str(file_path)] = local_backup
        except Exception as e:
            errors.append(str(e))

    if files_modified:
        build_error = _verify_build(target_path, files_modified)
        if build_error:
            for fp in files_modified:
                Path(fp).write_bytes(backup_for[fp].read_bytes())
            errors.append(
                f"Reverted {len(files_modified)} file(s) — patches broke the build: {build_error}"
            )
            files_modified = []

    return {
        "files_modified": files_modified,
        "backup_paths": backup_paths,
        "patch_errors": state.get("patch_errors", []) + errors,
        "last_modified_files": files_modified,
    }
