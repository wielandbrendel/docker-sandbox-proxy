"""Stop an agent sandbox."""

from __future__ import annotations

import time

import typer

from sandbox.config.loader import get_agent_dir, load_agent_config
from sandbox.docker.client import docker_sandbox_exec, docker_sandbox_stop
from sandbox.gmail_filter.manager import GmailFilterManager


def stop(
    name: str = typer.Argument(..., help="Agent name"),
) -> None:
    """Stop an agent sandbox."""
    config = load_agent_config(name)
    agent_dir = get_agent_dir(name)

    # 1. Stop OpenClaw (graceful)
    typer.echo("Stopping OpenClaw...")
    try:
        docker_sandbox_exec(name, "pkill -f 'openclaw gateway' || true", timeout=10)
        time.sleep(3)
        docker_sandbox_exec(name, "pkill -9 -f 'openclaw gateway' || true", timeout=5)
    except Exception:
        pass

    # 2. Stop sandbox VM
    typer.echo(f"Stopping sandbox '{name}'...")
    docker_sandbox_stop(name)

    # 3. Stop gmail-filter
    if config.gmail_filter.enabled:
        typer.echo("Stopping gmail-filter...")
        gmail_mgr = GmailFilterManager(
            agent_name=name,
            host_port=config.gmail_filter.host_port,
            certs_dir=agent_dir / "gmail-filter-certs",
        )
        gmail_mgr.stop()

    typer.echo(f"Agent '{name}' stopped.")
