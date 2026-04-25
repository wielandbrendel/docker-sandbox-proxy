"""Manage gmail-filter Docker containers on the host."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from sandbox.docker.client import (
    docker_build,
    docker_image_exists,
    docker_inspect,
    docker_logs,
    docker_rm,
    docker_run,
    docker_stop,
)

GMAIL_FILTER_IMAGE = "gmail-filter:latest"


class GmailFilterManager:
    def __init__(self, agent_name: str, host_port: int, certs_dir: Path):
        self.agent_name = agent_name
        self.host_port = host_port
        self.certs_dir = certs_dir
        self.container_name = f"gmail-filter-{agent_name}"

    def ensure_image(self, build_context: Path) -> None:
        if not docker_image_exists(GMAIL_FILTER_IMAGE):
            docker_build(str(build_context), GMAIL_FILTER_IMAGE)

    def start(self, http_port: int = 8080) -> None:
        """Start the gmail-filter with both HTTPS and HTTP ports.

        Args:
            http_port: HTTP port for sandbox agents (avoids TLS cert issues).
                       Sandbox agents access via http://host.docker.internal:<http_port>.
                       The sandbox proxy rewrites this to localhost:<http_port>.
        """
        if self.is_running():
            return
        docker_rm(self.container_name, force=True)
        self.certs_dir.mkdir(parents=True, exist_ok=True)
        docker_run(
            name=self.container_name,
            image=GMAIL_FILTER_IMAGE,
            ports={self.host_port: 443, http_port: 8080},
            volumes={str(self.certs_dir): "/certs"},
            restart="unless-stopped",
            detach=True,
        )

    def stop(self) -> None:
        docker_stop(self.container_name)
        docker_rm(self.container_name, force=True)

    def is_running(self) -> bool:
        info = docker_inspect(self.container_name)
        if info is None:
            return False
        return info.get("State", {}).get("Running", False)

    def wait_for_healthy(self, timeout: int = 30) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                result = subprocess.run(
                    ["openssl", "s_client", "-connect", f"127.0.0.1:{self.host_port}",
                     "-servername", "gmail.googleapis.com"],
                    input=b"",
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            time.sleep(1)
        return False

    def logs(self, follow: bool = False, tail: int = 100) -> None:
        docker_logs(self.container_name, follow=follow, tail=tail)
