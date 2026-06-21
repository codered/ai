from click.testing import CliRunner

from nasa_dod_agent.cli import init_config, main, restore
from nasa_dod_agent.cli import status


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "review" in result.output
    assert "restore" in result.output

def test_review_command_needs_path():
    runner = CliRunner()
    result = runner.invoke(main, ["review"])
    # Should fail without PATH argument
    assert result.exit_code != 0

def test_init_config_creates_file(temp_project):
    runner = CliRunner()
    result = runner.invoke(init_config, [str(temp_project)])
    assert result.exit_code == 0
    assert (temp_project / ".nasa-dod-agent" / "config.yaml").exists()

def test_restore_undoes_changes(temp_project):
    target = temp_project / "main.py"
    target.write_text("original\n")
    backup_dir = temp_project / ".nasa-dod-agent" / "backups"
    backup_dir.mkdir(parents=True)
    (backup_dir / "main.py.bak").write_text("backup content\n")

    runner = CliRunner()
    result = runner.invoke(restore, [str(temp_project)])
    assert result.exit_code == 0
    assert "backup content" in target.read_text()


def test_review_accepts_a_single_file_path(temp_project, monkeypatch):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")
    # Must be deterministic regardless of the ambient shell's env — this
    # test asserts on the missing-key error path, so the key must be
    # actually absent here even if the developer's own shell has one set.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    runner = CliRunner()
    result = runner.invoke(main, ["review", str(target), "--no-interactive"])

    # Fails fast on the missing OPENAI_API_KEY check rather than on Click's
    # own path validation — proves Click accepted a file path argument.
    assert "OPENAI_API_KEY" in result.output
    assert (temp_project / ".nasa-dod-agent").exists()


def test_restore_accepts_a_single_file_path(temp_project):
    target = temp_project / "main.py"
    target.write_text("original\n")
    backup_dir = temp_project / ".nasa-dod-agent" / "backups"
    backup_dir.mkdir(parents=True)
    (backup_dir / "main.py.bak").write_text("backup content\n")

    runner = CliRunner()
    result = runner.invoke(restore, [str(target)])

    assert result.exit_code == 0
    assert "backup content" in target.read_text()


def test_status_accepts_a_single_file_path(temp_project):
    target = temp_project / "main.py"
    target.write_text("x = 1\n")
    state_dir = temp_project / ".nasa-dod-agent"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text('{"iteration": 3, "p0_count": 1}')

    runner = CliRunner()
    result = runner.invoke(status, [str(target)])

    assert result.exit_code == 0
    assert "Iteration: 3" in result.output
