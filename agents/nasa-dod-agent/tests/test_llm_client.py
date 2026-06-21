import os
from unittest.mock import patch

from nasa_dod_agent.llm_client import LLMClient


def test_from_env_reads_openai_vars():
    env = {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "o3-mini"}
    with patch.dict(os.environ, env, clear=False):
        client = LLMClient(api_key="test-key", model="o3-mini")
        assert client.api_key == "test-key"
        assert client.model == "o3-mini"

def test_from_env_defaults():
    with patch.dict(os.environ, {}, clear=True):
        client = LLMClient(api_key="x")
        assert client.model == "gpt-4o"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.temperature == 0.0
