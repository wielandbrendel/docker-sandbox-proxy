"""Wrapper for docker and docker sandbox CLI commands."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def _run(
    cmd: list[str],
    capture: bool = True,
    check: bool = True,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


# ── Docker Sandbox commands ───────────────────────────────────────


def check_sandbox_support() -> bool:
    try:
        _run(["docker", "sandbox", "ls"], timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def docker_sandbox_create(
    name: str, workspaces: list[str], template: str | None = None
) -> None:
    cmd = ["docker", "sandbox", "create", "--name", name]
    if template:
        cmd.extend(["-t", template])
    cmd.append("shell")
    cmd.extend(workspaces)
    _run(cmd)


def docker_sandbox_stop(name: str) -> None:
    _run(["docker", "sandbox", "stop", name], check=False)


def docker_sandbox_rm(name: str) -> None:
    _run(["docker", "sandbox", "rm", name], check=False)


def docker_sandbox_exec(
    name: str,
    command: str,
    capture: bool = True,
    timeout: int = 300,
    user: str = "agent",
) -> subprocess.CompletedProcess:
    return _run(
        ["docker", "sandbox", "exec", "-u", user, name, "bash", "-c", command],
        capture=capture,
        timeout=timeout,
    )


def docker_sandbox_exec_interactive(name: str, user: str = "agent") -> None:
    os.execvp("docker", ["docker", "sandbox", "exec", "-it", "-u", user, name, "bash"])


def docker_sandbox_ls() -> list[dict]:
    result = _run(["docker", "sandbox", "ls", "--format", "json"], check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def docker_sandbox_proxy(
    name: str,
    policy: str | None = None,
    allow_hosts: list[str] | None = None,
    block_hosts: list[str] | None = None,
    bypass_hosts: list[str] | None = None,
) -> None:
    # Ensure sandbox is running (proxy commands require a running VM)
    _run(["docker", "sandbox", "exec", name, "true"], check=False, timeout=30)
    if policy:
        _run(["docker", "sandbox", "network", "proxy", name, "--policy", policy])
    for host in (allow_hosts or []):
        _run(["docker", "sandbox", "network", "proxy", name, "--allow-host", host])
    for host in (block_hosts or []):
        _run(["docker", "sandbox", "network", "proxy", name, "--block-host", host])
    for host in (bypass_hosts or []):
        _run(["docker", "sandbox", "network", "proxy", name, "--bypass-host", host])


# ── Regular Docker commands ───────────────────────────────────────


def docker_run(
    name: str,
    image: str,
    ports: dict[int, int] | None = None,
    volumes: dict[str, str] | None = None,
    restart: str | None = None,
    detach: bool = True,
) -> None:
    cmd = ["docker", "run"]
    if detach:
        cmd.append("-d")
    cmd.extend(["--name", name])
    if restart:
        cmd.extend(["--restart", restart])
    for host_port, container_port in (ports or {}).items():
        cmd.extend(["-p", f"{host_port}:{container_port}"])
    for host_path, container_path in (volumes or {}).items():
        cmd.extend(["-v", f"{host_path}:{container_path}"])
    cmd.append(image)
    _run(cmd)


def docker_stop(name: str) -> None:
    _run(["docker", "stop", name], check=False)


def docker_rm(name: str, force: bool = False) -> None:
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    cmd.append(name)
    _run(cmd, check=False)


def docker_inspect(name: str) -> dict | None:
    result = _run(["docker", "inspect", name], check=False)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data[0] if data else None
    except (json.JSONDecodeError, IndexError):
        return None


def docker_image_exists(tag: str) -> bool:
    result = _run(["docker", "image", "inspect", tag], check=False)
    return result.returncode == 0


def docker_build(context: str, tag: str) -> None:
    _run(["docker", "build", "-t", tag, context])


def docker_logs(name: str, follow: bool = False, tail: int = 100) -> None:
    cmd = ["docker", "logs", "--tail", str(tail)]
    if follow:
        cmd.append("-f")
    cmd.append(name)
    _run(cmd, capture=False, check=False)
