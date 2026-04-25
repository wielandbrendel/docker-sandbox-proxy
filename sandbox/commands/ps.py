"""List all agent sandboxes and their status."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from sandbox.config.loader import get_project_root
from sandbox.docker.client import docker_inspect, docker_sandbox_ls
from sandbox.registry import Registry

console = Console()


def ps() -> None:
    """List all agent sandboxes and their status."""
    registry = Registry(get_project_root() / "registry.json")
    agents = registry.list_agents()
    if not agents:
        typer.echo("No agents registered.")
        return

    sandboxes = {s.get("name", ""): s for s in docker_sandbox_ls()}

    table = Table(title="Agent Sandboxes")
    table.add_column("Name")
    table.add_column("Sandbox VM")
    table.add_column("Gmail Filter")
    table.add_column("Gmail Port")

    for name in agents:
        info = registry.get(name)
        vm_status = "running" if name in sandboxes else "stopped"
        gf_status = "n/a"
        gf_port = "-"
        if info and info.get("gmail_filter_container"):
            container = docker_inspect(info["gmail_filter_container"])
            gf_status = "running" if container and container.get("State", {}).get("Running") else "stopped"
            gf_port = str(info.get("gmail_filter_port", "-"))
        table.add_row(name, vm_status, gf_status, gf_port)

    console.print(table)
