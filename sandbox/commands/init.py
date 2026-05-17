"""Scaffold a new agent configuration."""

from __future__ import annotations

import re
from pathlib import Path

import typer

from sandbox.config.loader import get_project_root, get_sandboxes_dir
from sandbox.registry import Registry

_DEFAULT_AGENT_YAML = """\
name: {name}
description: "{description}"

openclaw:
  version: "2026.5.7"
  port: 18789

workspaces:
  - {agent_dir}

env:
  TZ: "Europe/Berlin"

env_file: .env

gmail_filter:
  enabled: false
  host_port: {gmail_port}
  http_port: {gmail_http_port}

network:
  policy: deny
  allow:
    - "api.telegram.org"
    - "*.api.telegram.org"
    - "t.me"
    - "*.t.me"
    - "*.openai.com"
    - "chatgpt.com"
    - "*.chatgpt.com"
    - "*.github.com"
    - "*.githubusercontent.com"
    - "*.githubassets.com"
    - "*.npmjs.org"
    - "*.npmjs.com"
    - "*.pypi.org"
    - "*.accounts.google.com"
    - "oauth2.googleapis.com"

resources:
  cpus: "4"
  memory: "8g"

restart_policy: unless-stopped
"""


def init(
    name: str = typer.Argument(..., help="Agent name (lowercase, hyphens ok)"),
    description: str = typer.Option("", help="Agent description"),
) -> None:
    """Scaffold a new agent configuration directory."""
    if not re.match(r"^[a-z0-9-]+$", name):
        typer.echo(f"Error: name must match [a-z0-9-], got '{name}'", err=True)
        raise typer.Exit(1)

    sandboxes_dir = get_sandboxes_dir()
    agent_dir = sandboxes_dir / name

    if agent_dir.exists():
        typer.echo(f"Error: {agent_dir} already exists", err=True)
        raise typer.Exit(1)

    # Create directory structure
    agent_dir.mkdir(parents=True)
    (agent_dir / "workspace").mkdir()
    (agent_dir / "openclaw-data").mkdir()
    (agent_dir / "gmail-filter-certs").mkdir()

    # Allocate ports
    registry = Registry(get_project_root() / "registry.json")
    gmail_port = registry.find_available_port(base=8443)
    gmail_http_port = gmail_port - 8443 + 8080  # offset: 8443→8080, 8444→8081, etc.

    # Generate agent.yaml
    content = _DEFAULT_AGENT_YAML.format(
        name=name,
        description=description or f"{name} agent",
        agent_dir=str(agent_dir),
        gmail_port=gmail_port,
        gmail_http_port=gmail_http_port,
    )
    (agent_dir / "agent.yaml").write_text(content)

    # Create empty .env
    (agent_dir / ".env").write_text("# Agent secrets — ${VAR} references expanded at load time\n")

    # Copy proxy-bootstrap.cjs template if present for legacy/custom agents.
    template = get_project_root() / "sandboxes" / "example-mail" / "proxy-bootstrap.cjs"
    if template.exists():
        import shutil
        shutil.copy2(template, agent_dir / "proxy-bootstrap.cjs")

    # Register
    registry.register(name, gmail_filter_port=gmail_port)

    typer.echo(f"Created {agent_dir}")
    typer.echo(f"  Gmail filter HTTPS port: {gmail_port}")
    typer.echo(f"  Gmail filter HTTP port: {gmail_http_port}")
    typer.echo(f"  Edit agent.yaml to configure, then run: sandbox start {name}")
    typer.echo(f"  After start, run: sandbox shell {name}")
    typer.echo(f"    Then: openclaw onboard")
