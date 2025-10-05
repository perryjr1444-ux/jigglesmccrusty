"""Deterministic token replacement utilities."""
from __future__ import annotations

from typing import Dict

from .hasher import digest_text


class Redactor:
    """Performs deterministic redaction using SHA-256 derived tokens."""

    def __init__(self, salt: str = "mac-blue-team") -> None:
        self.salt = salt

    def redact(self, secrets: Dict[str, str]) -> Dict[str, str]:
        """Return a mapping with values replaced by stable redaction tokens."""
        return {
            key: digest_text(f"{self.salt}:{value}")[:12]
            for key, value in secrets.items()
        }
