"""Preflight checks for `sandbox check <name>`.

Each check is a small function returning a CheckResult. The CLI
runs all relevant checks and prints them as checkmark/X with fix hints.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import typer


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str
    fix_hint: str | None


@dataclass
class Summary:
    passed: int
    failed: int
    results: list[CheckResult]

    @property
    def ok(self) -> bool:
        return self.failed == 0


def check_env_file(agent_dir: Path) -> CheckResult:
    env = agent_dir / ".env"
    if not env.exists():
        return CheckResult(
            name=".env file",
            ok=False,
            message=f".env not found at {env}",
            fix_hint=f"cp {agent_dir}/.env.example {env} and fill in values",
        )
    return CheckResult(".env file", True, str(env), None)


def check_required_env_vars(env: dict, required: list[str]) -> CheckResult:
    missing = [v for v in required if not env.get(v)]
    if missing:
        return CheckResult(
            name="required env vars",
            ok=False,
            message=f"missing: {', '.join(missing)}",
            fix_hint="set these in .env",
        )
    return CheckResult("required env vars", True, "all set", None)


def check_base_image(image: str = "sandbox-template:latest") -> CheckResult:
    r = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return CheckResult(
            name=f"base image {image}",
            ok=False,
            message="not built",
            fix_hint=f"docker build -t {image} base-image/sandbox-template/",
        )
    return CheckResult(f"base image {image}", True, "present", None)


def check_telegram_bot_token(token: str) -> CheckResult:
    """Optional: verify token reachable via getMe."""
    if not token:
        return CheckResult(
            name="telegram getMe",
            ok=False,
            message="no token provided",
            fix_hint="set TELEGRAM_BOT_TOKEN in .env",
        )
    r = subprocess.run(
        ["curl", "-sSf", "--max-time", "5",
         f"https://api.telegram.org/bot{token}/getMe"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return CheckResult(
            "telegram getMe",
            False,
            "API call failed",
            "check TELEGRAM_BOT_TOKEN value (BotFather -> /mybots -> API token)",
        )
    try:
        data = json.loads(r.stdout)
        if not data.get("ok"):
            return CheckResult(
                "telegram getMe",
                False,
                f"API returned ok=false: {data}",
                "regenerate token via @BotFather -> /revoke",
            )
    except json.JSONDecodeError:
        return CheckResult(
            "telegram getMe", False, "invalid JSON response", None,
        )
    return CheckResult(
        "telegram getMe", True, f"@{data['result']['username']}", None,
    )


def run_checks(checks: Iterable[Callable[[], CheckResult]]) -> Summary:
    results = [c() for c in checks]
    passed = sum(1 for r in results if r.ok)
    failed = sum(1 for r in results if not r.ok)
    return Summary(passed=passed, failed=failed, results=results)


def format_summary(summary: Summary) -> str:
    lines = []
    for r in summary.results:
        icon = "OK" if r.ok else "FAIL"
        lines.append(f"[{icon}] {r.name}: {r.message}")
        if not r.ok and r.fix_hint:
            lines.append(f"   fix: {r.fix_hint}")
    lines.append("")
    lines.append(f"{summary.passed} passed, {summary.failed} failed")
    return "\n".join(lines)


def check(
    name: str = typer.Argument(help="Agent name"),
) -> None:
    """Run preflight checks for an agent without starting it."""
    import os
    import re

    from sandbox.config.loader import get_sandboxes_dir, load_agent_config

    agent_dir = get_sandboxes_dir() / name

    if not agent_dir.exists():
        typer.echo(f"Error: Agent '{name}' not found")
        raise typer.Exit(1)

    try:
        cfg = load_agent_config(name)
    except Exception as e:
        typer.echo(f"Config error: {e}")
        raise typer.Exit(1)

    # Parse .env if present
    env_path = agent_dir / ".env"
    env: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")

    # Required vars from agent.yaml that look like ${VAR} refs
    raw = (agent_dir / "agent.yaml").read_text()
    required = sorted({m.group(1) for m in re.finditer(r"\$\{([A-Z_][A-Z0-9_]*)\}", raw)})

    checks: list[Callable[[], CheckResult]] = [
        lambda: check_env_file(agent_dir),
        lambda: check_required_env_vars({**os.environ, **env}, required),
        lambda: check_base_image(),
    ]

    if cfg.gmail_filter.enabled and env.get("TELEGRAM_BOT_TOKEN"):
        token = env["TELEGRAM_BOT_TOKEN"]
        checks.append(lambda: check_telegram_bot_token(token))

    summary = run_checks(checks)
    typer.echo(format_summary(summary))
    raise typer.Exit(0 if summary.ok else 1)
