from nasa_dod_agent.standards_loader import StandardsLoader


def test_load_prompts_exist():
    loader = StandardsLoader()
    prompt = loader.get_reviewer_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 100


def test_get_severity_guide():
    loader = StandardsLoader()
    guide = loader.get_severity_guide()
    assert isinstance(guide, str)
    assert "P0" in guide
