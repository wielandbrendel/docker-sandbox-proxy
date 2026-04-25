"""Pydantic v2 models for agent.yaml."""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpenClawConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "2026.4.11"
    port: int = 18789


class NetworkConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: str = "deny"
    allow: list[str] = Field(default_factory=list)

    @field_validator("policy")
    @classmethod
    def validate_policy(cls, v: str) -> str:
        if v not in ("deny", "allow"):
            raise ValueError(f"network.policy must be 'deny' or 'allow', got '{v}'")
        return v


class GmailFilterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    host_port: int = 8443   # HTTPS port (for direct host access)
    http_port: int = 8080   # HTTP port (for sandbox agent access via localhost)


class ResourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpus: str = "4"
    memory: str = "8g"


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""

    openclaw: OpenClawConfig = Field(default_factory=OpenClawConfig)

    workspaces: list[str] = Field(default_factory=list)

    env: dict[str, str] = Field(default_factory=dict)
    env_file: str = ""

    gmail_filter: GmailFilterConfig = Field(default_factory=GmailFilterConfig)

    network: NetworkConfig = Field(default_factory=NetworkConfig)

    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    restart_policy: str = "unless-stopped"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(f"Agent name must match [a-z0-9-], got '{v}'")
        return v
