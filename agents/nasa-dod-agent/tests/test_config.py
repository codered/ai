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

def test_init_config_writes_review_samples(temp_project):
    ConfigLoader.init_config(temp_project)
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    assert "review_samples: 1" in config_path.read_text()

def test_load_review_samples_from_llm_section(temp_project):
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("llm:\n  review_samples: 3\n")
    loaded = ConfigLoader.load(temp_project)
    assert loaded.review_samples == 3


def test_init_config_writes_new_limit_fields(temp_project):
    ConfigLoader.init_config(temp_project)
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    content = config_path.read_text()
    assert "max_iterations: 5" in content
    assert "max_fix_attempts_per_chunk: 2" in content
    assert "max_total_fix_attempts: 20" in content

def test_load_new_limit_fields_from_yaml(temp_project):
    config_path = temp_project / ".nasa-dod-agent" / "config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "limits:\n"
        "  max_fix_attempts_per_chunk: 4\n"
        "  max_total_fix_attempts: 50\n"
    )
    loaded = ConfigLoader.load(temp_project)
    assert loaded.max_fix_attempts_per_chunk == 4
    assert loaded.max_total_fix_attempts == 50
