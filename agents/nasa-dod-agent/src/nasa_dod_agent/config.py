"""Load and save per-project rubric configuration."""

from pathlib import Path
from typing import Optional

import yaml

from nasa_dod_agent.models import RubricConfig

DEFAULT_CONFIG = RubricConfig()


class ConfigLoader:
    """Loads rubric config from .nasa-dod-agent/config.yaml."""

    CONFIG_DIR = ".nasa-dod-agent"
    CONFIG_FILENAME = "config.yaml"

    @staticmethod
    def _config_dir(project_path: Path) -> Path:
        return project_path / ConfigLoader.CONFIG_DIR

    @staticmethod
    def _config_path(project_path: Path) -> Path:
        return ConfigLoader._config_dir(project_path) / ConfigLoader.CONFIG_FILENAME

    @classmethod
    def _default_config(cls) -> RubricConfig:
        return RubricConfig()

    @classmethod
    def load(cls, project_path: Path) -> Optional[RubricConfig]:
        path = cls._config_path(project_path)
        if not path.exists():
            return None
        raw = yaml.safe_load(path.read_text())
        if raw is None:
            return None
        # Flatten nested keys for compatibility with our model
        flat: dict = {}
        if "rubric" in raw and isinstance(raw["rubric"], dict):
            flat.update(raw["rubric"])
        if "limits" in raw and isinstance(raw["limits"], dict):
            flat.update(raw["limits"])
        if "llm" in raw and isinstance(raw["llm"], dict):
            flat.update(raw["llm"])
        flat.update({k: v for k, v in raw.items() if k not in ("rubric", "limits", "llm")})
        return RubricConfig(**flat)

    @classmethod
    def init_config(cls, project_path: Path) -> RubricConfig:
        """Create default config.yaml in project if it doesn't exist."""
        config_dir = cls._config_dir(project_path)
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / cls.CONFIG_FILENAME
        default = cls._default_config()
        config_path.write_text(
            "rubric:\n"
            f"  max_p0: {default.max_p0}\n"
            f"  max_p1: {default.max_p1}\n"
            f"  max_p2: {default.max_p2}\n"
            f"  max_p3: {default.max_p3}\n"
            "  # 0 = fix nothing, 1 = fix P0+P1, 2 = fix P0+P1+P2, 3 = fix everything\n"
            f"  fix_threshold: {default.fix_threshold}\n"
            "\n"
            "limits:\n"
            f"  max_iterations: {default.max_iterations}\n"
            "\n"
            "llm:\n"
            f"  temperature: {default.temperature}\n"
            f"  max_tokens: {default.max_tokens}\n"
            "\n"
            "exclude:\n"
            "  - \"**/node_modules/**\"\n"
            "  - \"**/.git/**\"\n"
            "  - \"**/venv/**\"\n"
            "  - \"**/__pycache__/**\"\n"
        )
        return default
