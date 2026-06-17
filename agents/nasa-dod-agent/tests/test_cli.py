from click.testing import CliRunner

from nasa_dod_agent.cli import init_config, main, restore


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
