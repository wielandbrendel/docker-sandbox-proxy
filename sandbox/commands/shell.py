"""Open interactive shell in sandbox VM."""

from __future__ import annotations

import typer

from sandbox.docker.client import docker_sandbox_exec_interactive


def shell(
    name: str = typer.Argument(..., help="Agent name"),
    root: bool = typer.Option(False, "--root", help="Open shell as root"),
) -> None:
    """Open interactive shell in sandbox VM."""
    docker_sandbox_exec_interactive(name, user="root" if root else "agent")
