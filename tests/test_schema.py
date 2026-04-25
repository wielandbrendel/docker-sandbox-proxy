import pytest
from sandbox.config.schema import AgentConfig, OpenClawConfig, NetworkConfig, GmailFilterConfig, ResourceConfig


def test_minimal_config():
    cfg = AgentConfig(name="test-agent")
    assert cfg.name == "test-agent"
    assert cfg.description == ""
    assert cfg.openclaw.version == "2026.4.11"
    assert cfg.openclaw.port == 18789
    assert cfg.workspaces == []
    assert cfg.env == {}
    assert cfg.gmail_filter.enabled is False
    assert cfg.network.policy == "deny"
    assert cfg.network.allow == []
    assert cfg.resources.cpus == "4"
    assert cfg.resources.memory == "8g"
    assert cfg.restart_policy == "unless-stopped"


def test_name_validation_rejects_uppercase():
    with pytest.raises(ValueError, match="must match"):
        AgentConfig(name="BadName")


def test_name_validation_rejects_spaces():
    with pytest.raises(ValueError, match="must match"):
        AgentConfig(name="bad name")


def test_name_validation_allows_hyphens():
    cfg = AgentConfig(name="my-agent-1")
    assert cfg.name == "my-agent-1"


def test_full_config():
    cfg = AgentConfig(
        name="openclaw-mail",
        description="Test agent",
        openclaw=OpenClawConfig(version="2026.4.0", port=19000),
        workspaces=["~/workspace", "~/docs:ro"],
        env={"TZ": "Europe/Berlin"},
        env_file=".env",
        gmail_filter=GmailFilterConfig(enabled=True, host_port=8443),
        network=NetworkConfig(policy="deny", allow=["*.github.com"]),
        resources=ResourceConfig(cpus="2", memory="4g"),
    )
    assert cfg.openclaw.version == "2026.4.0"
    assert cfg.openclaw.port == 19000
    assert cfg.gmail_filter.host_port == 8443
    assert cfg.network.allow == ["*.github.com"]


def test_network_policy_validation():
    with pytest.raises(ValueError):
        NetworkConfig(policy="invalid")


def test_gmail_filter_default_ports():
    cfg = GmailFilterConfig(enabled=True)
    assert cfg.host_port == 8443
    assert cfg.http_port == 8080
