"""Click CLI entry point for nasa-dod-agent."""

import os
import shutil
from pathlib import Path

import click
from pydantic import ValidationError

from nasa_dod_agent.config import ConfigLoader
from nasa_dod_agent.graph import build_graph
from nasa_dod_agent.state import GraphState


def _archive_checkpoints(checkpoint_dir: Path) -> None:
    """Move everything in checkpoint_dir into checkpoint_dir/archive/.

    Uses copy-then-delete rather than ``shutil.move`` so it also works
    when the destination is on a different filesystem (e.g. in tests).
    """
    if not checkpoint_dir.exists():
        return

    archive = checkpoint_dir / "archive"
    archive.mkdir(parents=True, exist_ok=True)

    for item in checkpoint_dir.iterdir():
        if item.name == "archive":
            continue
        dest = archive / item.name
        if dest.exists():
            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
        if item.is_dir():
            shutil.copytree(item, dest)
            shutil.rmtree(item)
        else:
            shutil.copy2(item, dest)
            item.unlink()


_STOP_MESSAGES = {
    "rubric_passed": "Rubric passed: YES",
    "max_iterations": (
        "Rubric NOT met — hit max_iterations without converging. "
        "Findings still exceed the configured thresholds."
    ),
    "no_fixable_findings": (
        "Rubric NOT met — no fixable findings. Remaining findings are all "
        "below fix_threshold. Adjust fix_threshold or max_pX in config.yaml."
    ),
}


def _stop_message(stop_reason: str | None) -> str:
    return _STOP_MESSAGES.get(stop_reason, "Rubric NOT met.")


@click.group()
def main():
    """NASA/DoD Deep Agent — iterative code review with auto-fix."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--full", is_flag=True, help="Force full scan, ignore checkpoints")
@click.option("--max-rounds", type=int, default=None, help="Override max_iterations")
@click.option("--dry-run", is_flag=True, help="Generate fixes but don't write")
@click.option("--reset", is_flag=True, help="Delete checkpoint, start fresh")
@click.option("--no-interactive", is_flag=True, help="Skip resume prompt")
def review(path, full, max_rounds, dry_run, reset, no_interactive):
    """Run the NASA/DOD review loop on a directory."""
    project_path = Path(path)
    config_dir = project_path / ".nasa-dod-agent"
    checkpoint_dir = str(config_dir / "checkpoints")

    checkpoint_exists = (
        (config_dir / "checkpoints").exists()
        and any((config_dir / "checkpoints").iterdir())
    )

    if reset:
        _archive_checkpoints(config_dir / "checkpoints")
        click.echo("Checkpoint reset. Starting fresh.")

    elif checkpoint_exists and not no_interactive and not full:
        click.echo("In-progress review found for this directory.")
        click.echo("Use --reset to start fresh or --no-interactive to resume silently.")
        return

    try:
        config = ConfigLoader.load(project_path)
    except ValidationError as e:
        click.echo(f"Invalid {config_dir / 'config.yaml'}:")
        for err in e.errors():
            field = ".".join(str(p) for p in err["loc"])
            click.echo(f"  {field}: {err['msg']} (got {err.get('input')!r})")
        raise click.Abort()

    if config is None:
        config = ConfigLoader.init_config(project_path)
        click.echo(f"Created default config at {config_dir / 'config.yaml'}")

    if max_rounds is not None:
        config.max_iterations = max_rounds

    if not os.environ.get("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY environment variable is required")
        raise click.Abort()

    state: GraphState = {
        "target_path": str(project_path.absolute()),
        "review_mode": "full" if full or not checkpoint_exists else "incremental",
        "iteration": 0,
        "max_iterations": config.max_iterations,
        "findings": [],
        "files_reviewed": [],
        "last_modified_files": [],
        "config": config,
        "rubric_passed": False,
        "stop_reason": None,
        "p0_count": 0,
        "p1_count": 0,
        "p2_count": 0,
        "p3_count": 0,
        "patches": [],
        "patch_errors": [],
        "files_modified": [],
        "backup_paths": [],
    }

    graph = build_graph(checkpoint_dir)
    thread_id = f"review-{project_path.name}"
    final_state = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})

    click.echo("\n--- Review Complete ---")
    click.echo(f"Iterations: {final_state['iteration']}")
    click.echo(
        f"P0: {final_state['p0_count']}  P1: {final_state['p1_count']}  "
        f"P2: {final_state['p2_count']}  P3: {final_state['p3_count']}"
    )
    click.echo(_stop_message(final_state.get("stop_reason")))
    if final_state.get("patch_errors"):
        click.echo(f"Patch errors: {len(final_state['patch_errors'])}")
        for err in final_state["patch_errors"]:
            click.echo(f"  - {err}")

    _archive_checkpoints(config_dir / "checkpoints")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def restore(path):
    """Undo all agent changes (restore .bak files)."""
    project_path = Path(path)
    backup_dir = project_path / ".nasa-dod-agent" / "backups"

    if not backup_dir.exists():
        click.echo("No backups found.")
        return

    count = 0
    for backup in backup_dir.glob("*.bak"):
        original_name = backup.stem
        candidates = list(project_path.rglob(original_name))
        candidates = [c for c in candidates if ".nasa-dod-agent" not in str(c)]
        if candidates:
            original = candidates[0]
            original.write_bytes(backup.read_bytes())
            count += 1
            click.echo(f"Restored {original}")

    click.echo(f"Restored {count} file(s).")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def status(path):
    """Show current review state."""
    project_path = Path(path)
    state_file = project_path / ".nasa-dod-agent" / "state.json"
    if state_file.exists():
        import json
        data = json.loads(state_file.read_text())
        click.echo(f"Current review state for {project_path}:")
        click.echo(f"  Iteration: {data.get('iteration', 'N/A')}")
        click.echo(f"  P0: {data.get('p0_count', 0)}")
        click.echo(f"  P1: {data.get('p1_count', 0)}")
        click.echo(f"  {_stop_message(data.get('stop_reason'))}")
    else:
        click.echo("No active review state found.")


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def init_config(path):
    """Generate a default config.yaml."""
    project_path = Path(path)
    ConfigLoader.init_config(project_path)
    click.echo(f"Created default config at {project_path / '.nasa-dod-agent' / 'config.yaml'}")


if __name__ == "__main__":
    main()
