"""Destroy an agent sandbox completely."""

from __future__ import annotations

import shutil

import typer

from sandbox.commands.stop import stop as _stop_impl
from sandbox.config.loader import get_agent_dir, get_project_root
from sandbox.docker.client import docker_rm, docker_sandbox_rm
from sandbox.registry import Registry


def destroy(
    name: str = typer.Argument(..., help="Agent name"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip confirmation prompt"),
    purge: bool = typer.Option(False, "--purge", help="Also remove agent directory"),
) -> None:
    """Destroy an agent sandbox completely."""
    if not yes:
        confirm = typer.confirm(f"Destroy agent '{name}'? This removes the sandbox VM and gmail-filter container.")
        if not confirm:
            raise typer.Abort()

    # Stop everything
    try:
        _stop_impl(name)
    except Exception:
        pass

    # Remove sandbox VM
    typer.echo(f"Removing sandbox VM '{name}'...")
    docker_sandbox_rm(name)

    # Remove gmail-filter container
    registry = Registry(get_project_root() / "registry.json")
    info = registry.get(name)
    if info and info.get("gmail_filter_container"):
        docker_rm(info["gmail_filter_container"], force=True)

    # Unregister
    registry.unregister(name)

    # Remove directory
    if purge:
        agent_dir = get_agent_dir(name)
        if agent_dir.exists():
            shutil.rmtree(agent_dir)
            typer.echo(f"Removed {agent_dir}")

    typer.echo(f"Agent '{name}' destroyed.")
