"""Thin wrapper around langchain_openai.ChatOpenAI with env/config fallback."""

import os
from typing import Optional

from langchain_openai import ChatOpenAI

from nasa_dod_agent.models import RubricConfig


class LLMClient:
    """Factory + wrapper for the review LLM."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm: Optional[ChatOpenAI] = None

    @classmethod
    def from_env(cls, config: Optional[RubricConfig] = None) -> "LLMClient":
        """Build client from environment + optional config overrides."""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")
        temp = config.temperature if config else 0.0
        max_tok = config.max_tokens if config else 4096
        return cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temp,
            max_tokens=max_tok,
        )

    def get_llm(self) -> ChatOpenAI:
        """Lazy-init the ChatOpenAI instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        return self._llm
