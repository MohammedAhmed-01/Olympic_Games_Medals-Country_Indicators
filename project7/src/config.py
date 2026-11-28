"""Typed configuration loading and validation."""

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Required configuration file is missing: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("config.yaml must contain a YAML mapping")
    return data


CONFIG = _load_config()


def get(section: str, key: str | None = None, default: Any = None) -> Any:
    """Get a required or optional configuration value."""
    if section not in CONFIG:
        raise KeyError(f"Missing required config section: {section}")
    value = CONFIG[section]
    if key is None:
        return value
    if not isinstance(value, dict) or key not in value:
        if default is not None:
            return default
        raise KeyError(f"Missing required config key: {section}.{key}")
    return value[key]
