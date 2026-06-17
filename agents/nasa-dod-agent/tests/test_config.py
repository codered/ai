from nasa_dod_agent.config import ConfigLoader


def test_default_config_values():
    config = ConfigLoader._default_config()
    assert config.max_p0 == 0
    assert config.max_p1 == 2
    assert config.fix_threshold == 1

def test_load_existing_config(temp_project):
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("rubric:\n  max_p0: 1\n  max_p1: 5\n")
    loaded = ConfigLoader.load(temp_project)
    assert loaded.max_p0 == 1
    assert loaded.max_p1 == 5

def test_init_config_creates_file(temp_project):
    config = ConfigLoader.init_config(temp_project)
    assert (temp_project / ".nasa-dod-agent" / "config.yaml").exists()
    assert config.max_p0 == 0
