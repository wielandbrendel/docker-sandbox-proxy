"""Start an agent: gmail-filter + Docker Sandbox + OpenClaw."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import typer

from sandbox.config.loader import get_agent_dir, get_project_root, load_agent_config
from sandbox.errors import die
from sandbox.docker.client import (
    check_sandbox_support,
    docker_sandbox_create,
    docker_sandbox_exec,
    docker_sandbox_proxy,
)
from sandbox.gmail_filter.manager import GmailFilterManager
from sandbox.init_script import SANDBOX_TEMPLATE, generate_init_script, generate_root_setup_script


def start(
    name: str = typer.Argument(..., help="Agent name"),
) -> None:
    """Start an agent sandbox."""
    # 1. Preflight
    if not check_sandbox_support():
        typer.echo("Error: Docker Sandbox support not found. Need Docker Desktop v4.40+.", err=True)
        raise typer.Exit(1)

    try:
        config = load_agent_config(name)
    except FileNotFoundError:
        die(
            f"No agent.yaml found for '{name}'",
            fix=f"sandbox init {name}  (or check the agent name)",
        )
    agent_dir = get_agent_dir(name)
    agent_dir_str = str(agent_dir)

    # 2. Start gmail-filter on host (if enabled)
    if config.gmail_filter.enabled:
        port = config.gmail_filter.host_port
        typer.echo(f"Starting gmail-filter (HTTP:{config.gmail_filter.http_port}, HTTPS:{port})...")
        gmail_mgr = GmailFilterManager(
            agent_name=name,
            host_port=port,
            certs_dir=agent_dir / "gmail-filter-certs",
        )
        gmail_mgr.ensure_image(get_project_root() / "base-image" / "gmail-filter")
        gmail_mgr.start(http_port=config.gmail_filter.http_port)
        typer.echo("  Waiting for gmail-filter to become healthy...")
        if not gmail_mgr.wait_for_healthy(timeout=30):
            die(
                "gmail-filter did not become healthy in 30s",
                fix=f"docker logs gmail-filter-{name}  (check for port conflicts or image issues)",
            )
        typer.echo("  gmail-filter healthy.")

    # 3. Create Docker Sandbox with custom template (idempotent)
    typer.echo(f"Creating Docker Sandbox '{name}'...")
    workspaces = []
    for ws in config.workspaces:
        if ":" in ws and ws.rsplit(":", 1)[1] in ("ro", "readonly"):
            path, _mode = ws.rsplit(":", 1)
            workspaces.append(str(Path(path).expanduser()) + ":ro")
        else:
            workspaces.append(str(Path(ws).expanduser()))
    if not workspaces:
        workspaces = [str(agent_dir)]
    try:
        docker_sandbox_create(name, workspaces, template=SANDBOX_TEMPLATE)
        typer.echo("  Sandbox created.")
    except Exception:
        typer.echo("  Sandbox already exists (reusing).")

    # 4. Configure proxy rules
    typer.echo("Configuring network proxy...")
    allow_hosts = list(config.network.allow)
    bypass_hosts = [
        "registry.npmjs.org",   # npm concurrency + MITM = ECONNRESET
        "api.telegram.org",     # OpenClaw's ProxyAgent fails TLS through MITM
        "chatgpt.com",          # OpenAI Codex API endpoint (Cloudflare challenge)
        "*.chatgpt.com",
        "*.openai.com",         # OpenAI OAuth refresh
    ]
    block_hosts = []

    if config.gmail_filter.enabled:
        # Allow agent to reach the filter via localhost (proxy rewrites host.docker.internal → localhost)
        allow_hosts.append(f"localhost:{config.gmail_filter.http_port}")
        # Block direct Gmail API access (must go through filter)
        block_hosts.extend([
            "gmail.googleapis.com",
            "content-gmail.googleapis.com",
            "www.googleapis.com",
        ])

    docker_sandbox_proxy(
        name,
        policy=config.network.policy,
        allow_hosts=allow_hosts if config.network.policy == "deny" else None,
        bypass_hosts=bypass_hosts,
        block_hosts=block_hosts if block_hosts else None,
    )
    typer.echo(f"  Policy: {config.network.policy}, {len(allow_hosts)} allowed, {len(block_hosts)} blocked.")

    # 5. Root setup (link configs, copy auth files)
    typer.echo("Running root setup...")
    root_script = generate_root_setup_script(config, agent_dir_str)
    root_script_path = agent_dir / "sandbox-root-setup.sh"
    root_script_path.write_text(root_script)
    root_script_path.chmod(0o755)
    result = subprocess.run(
        ["docker", "sandbox", "exec", "-u", "root", name, "bash", f"{agent_dir_str}/sandbox-root-setup.sh"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0 and "[root-setup]" not in result.stdout:
        typer.echo(f"Error: root setup failed:\n{result.stdout}\n{result.stderr}", err=True)
        raise typer.Exit(1)
    for line in (result.stdout or "").strip().split("\n"):
        if line.startswith("["):
            typer.echo(f"  {line}")

    # 6. Generate init script
    script = generate_init_script(config, agent_dir_str)
    init_script_path = agent_dir / "sandbox-init.sh"
    init_script_path.write_text(script)
    init_script_path.chmod(0o755)

    # 7. Verify OpenClaw started (entrypoint handles startup automatically)
    typer.echo("Waiting for OpenClaw to start via entrypoint...")
    time.sleep(10)
    result = docker_sandbox_exec(name, "pgrep -f 'openclaw gateway' || true", timeout=10)
    if result.stdout.strip():
        typer.echo(f"  OpenClaw running (PID {result.stdout.strip().split()[0]})")
    else:
        typer.echo("  Warning: OpenClaw may not have started. Check: sandbox logs <name>")

    typer.echo(f"Agent '{name}' started.")
