"""View current proxy rules for a sandbox."""

from __future__ import annotations

import subprocess

import typer


def proxy(
    name: str = typer.Argument(..., help="Agent name"),
) -> None:
    """View current proxy rules for a sandbox."""
    subprocess.run(
        ["docker", "sandbox", "network", "proxy", name],
        check=False,
    )
