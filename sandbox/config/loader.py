"""Load agent.yaml with env var expansion."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from sandbox.config.schema import AgentConfig

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def expand_env_vars(value: str) -> str:
    """Expand ${VAR_NAME} references from shell environment."""
    def _replace(match: re.Match) -> str:
        return os.environ.get(match.group(1), match.group(0))
    return _ENV_VAR_PATTERN.sub(_replace, value)


def _expand_recursive(obj):
    """Recursively expand env vars in strings within dicts/lists."""
    if isinstance(obj, str):
        return expand_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _expand_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_recursive(item) for item in obj]
    return obj


def get_project_root() -> Path:
    """Return the project root (docker-sandbox-proxy repo root)."""
    return Path(os.environ.get("SANDBOX_HOME", Path(__file__).resolve().parents[2]))


def get_sandboxes_dir() -> Path:
    """Return the sandboxes directory."""
    return get_project_root() / "sandboxes"


def get_agent_dir(name: str) -> Path:
    """Return the directory for a specific agent."""
    return get_sandboxes_dir() / name


def load_agent_config(name: str) -> AgentConfig:
    """Load and validate an agent's config."""
    agent_dir = get_agent_dir(name)
    config_path = agent_dir / "agent.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Agent config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    data = _expand_recursive(data)
    return AgentConfig(**data)
