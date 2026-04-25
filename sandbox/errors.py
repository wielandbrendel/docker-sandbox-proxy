"""User-friendly error helpers."""
from __future__ import annotations
import sys
from typing import NoReturn


class UserError(Exception):
    """Raised for expected, user-actionable errors. CLI exits 1 with the message."""

    def __init__(self, message: str, fix: str | None = None):
        self.message = message
        self.fix = fix
        super().__init__(message)


def die(message: str, fix: str | None = None) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    if fix:
        print(f"  fix: {fix}", file=sys.stderr)
    sys.exit(1)
