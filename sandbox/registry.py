"""Agent registry — tracks sandbox state in registry.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class Registry:
    def __init__(self, path: Path):
        self._path = path
        self._data: dict = {}
        if path.exists():
            self._data = json.loads(path.read_text())

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2) + "\n")

    def register(self, name: str, gmail_filter_port: int | None = None) -> None:
        self._data[name] = {
            "sandbox_name": name,
            "gmail_filter_port": gmail_filter_port,
            "gmail_filter_container": f"gmail-filter-{name}" if gmail_filter_port else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def unregister(self, name: str) -> None:
        self._data.pop(name, None)
        self._save()

    def get(self, name: str) -> dict | None:
        return self._data.get(name)

    def list_agents(self) -> list[str]:
        return list(self._data.keys())

    def is_port_in_use(self, port: int) -> bool:
        return any(
            info.get("gmail_filter_port") == port
            for info in self._data.values()
        )

    def find_available_port(self, base: int = 8443) -> int:
        port = base
        while self.is_port_in_use(port):
            port += 1
        return port
