"""Show resolved agent configuration."""

from __future__ import annotations

import typer
import yaml

from sandbox.config.loader import load_agent_config


def config(
    name: str = typer.Argument(..., help="Agent name"),
) -> None:
    """Show resolved agent configuration."""
    cfg = load_agent_config(name)
    typer.echo(yaml.dump(cfg.model_dump(), default_flow_style=False, sort_keys=False))
