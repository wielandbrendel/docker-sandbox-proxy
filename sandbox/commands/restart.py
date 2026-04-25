"""Restart an agent sandbox (stop + start)."""

from __future__ import annotations

import typer

from sandbox.commands.stop import stop as _stop_impl
from sandbox.commands.start import start as _start_impl


def restart(
    name: str = typer.Argument(..., help="Agent name"),
) -> None:
    """Restart an agent sandbox (stop + start)."""
    _stop_impl(name)
    _start_impl(name)
