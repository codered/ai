"""Node 4: apply_fixes — atomically apply patches to disk with backups."""

from pathlib import Path

from nasa_dod_agent.fix_parser import FixParser
from nasa_dod_agent.state import GraphState


def apply_fixes_node(state: GraphState) -> dict:
    """Apply patches to disk, creating backups in .nasa-dod-agent/backups/."""
    patches = state.get("patches", [])
    if not patches:
        return {"files_modified": [], "backup_paths": [], "patch_errors": [], "last_modified_files": []}

    target_path = Path(state["target_path"])
    backup_dir = target_path / ".nasa-dod-agent" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    parser = FixParser()
    files_modified = []
    backup_paths = []
    errors = []

    for patch in patches:
        try:
            file_path = Path(patch.file_path)
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                continue

            # Create backup in .nasa-dod-agent/backups/
            local_backup = backup_dir / (file_path.name + ".bak")
            local_backup.write_bytes(file_path.read_bytes())
            backup_paths.append(str(local_backup))

            parser.apply_patch(patch)
            files_modified.append(str(file_path))
        except Exception as e:
            errors.append(str(e))

    return {
        "files_modified": files_modified,
        "backup_paths": backup_paths,
        "patch_errors": state.get("patch_errors", []) + errors,
        "last_modified_files": files_modified,
    }
