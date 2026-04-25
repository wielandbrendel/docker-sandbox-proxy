import pytest
from pydantic import ValidationError
from sandbox.config.schema import AgentConfig


def test_unknown_top_level_key_rejected():
    with pytest.raises(ValidationError, match="extra"):
        AgentConfig(name="foo", reasoning={"effort": "medium"})


def test_unknown_nested_key_rejected():
    from sandbox.config.schema import OpenClawConfig
    with pytest.raises(ValidationError, match="extra"):
        OpenClawConfig(version="2026.4.11", port=18789, mystery_field=True)
