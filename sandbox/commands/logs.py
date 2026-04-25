"""View agent logs."""

from __future__ import annotations

import typer

from sandbox.config.loader import get_agent_dir, load_agent_config
from sandbox.docker.client import docker_sandbox_exec
from sandbox.gmail_filter.manager import GmailFilterManager


def logs(
    name: str = typer.Argument(..., help="Agent name"),
    service: str = typer.Option("agent", help="Service: agent or gmail-filter"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output"),
    tail: int = typer.Option(100, "--tail", help="Number of lines"),
) -> None:
    """View agent logs."""
    config = load_agent_config(name)
    if service == "gmail-filter":
        if not config.gmail_filter.enabled:
            typer.echo("Gmail filter not enabled for this agent.", err=True)
            raise typer.Exit(1)
        mgr = GmailFilterManager(name, config.gmail_filter.host_port, get_agent_dir(name) / "gmail-filter-certs")
        mgr.logs(follow=follow, tail=tail)
    else:
        agent_dir = get_agent_dir(name)
        log_dir = "~/.openclaw/logs"
        if follow:
            docker_sandbox_exec(name, f"tail -f $(ls -t {log_dir}/*.log 2>/dev/null | head -1) 2>/dev/null || echo 'No OpenClaw logs found.'", capture=False, timeout=600)
        else:
            docker_sandbox_exec(name, f"tail -n {tail} $(ls -t {log_dir}/*.log 2>/dev/null | head -1) 2>/dev/null || echo 'No OpenClaw logs found.'", capture=False, timeout=30)
