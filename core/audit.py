"""Tamper-evident append-only audit log backed by a Merkle tree."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from core.models import AuditEntry
from utils.hasher import digest_text, merkle_root


@dataclass
class AuditLog:
    path: Path = field(default_factory=lambda: Path("var/audit.log"))

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: List[AuditEntry] = []
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            for item in raw.get("entries", []):
                self._entries.append(AuditEntry(**item))

    @property
    def entries(self) -> List[AuditEntry]:
        return list(self._entries)

    @property
    def merkle_root(self) -> str:
        return merkle_root(entry.hash for entry in self._entries)

    def append(self, actor: str, action: str, details: Dict[str, object]) -> AuditEntry:
        index = len(self._entries)
        parent_hash = self._entries[-1].hash if self._entries else None
        payload = {
            "index": index,
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "details": details,
            "parent_hash": parent_hash,
        }
        entry_hash = digest_text(json.dumps(payload, sort_keys=True))
        entry = AuditEntry(hash=entry_hash, **payload)
        self._entries.append(entry)
        self._flush()
        return entry

    def _flush(self) -> None:
        data = {
            "entries": [entry.model_dump() for entry in self._entries],
            "root": self.merkle_root,
        }
        self.path.write_text(json.dumps(data, indent=2, default=str))
