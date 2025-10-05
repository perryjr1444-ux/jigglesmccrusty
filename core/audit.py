import json
import hashlib
import datetime
import os
from pathlib import Path

# Use a configurable log directory
_LOG_DIR = Path(os.environ.get("AUDIT_LOG_DIR", "/var/log/mac_blue_team_audit"))
try:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fall back to a temp directory if we don't have permissions
    _LOG_DIR = Path("/tmp/mac_blue_team_audit")
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


class AuditLog:
    """
    Append-only log. Every entry is hashed together with the previous
    entry to produce a simple Merkle-chain. The latest root hash can be
    periodically anchored (e.g., to a public blockchain or a signed
    timestamp authority) for extra non-repudiation.
    """

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.file = _LOG_DIR / f"{case_id}.log"

    def _last_hash(self) -> str:
        if not self.file.exists() or self.file.stat().st_size == 0:
            return "0" * 64
        with self.file.open("rb") as f:
            f.seek(-130, 2)  # each line ends with "... <hash>\n"
            tail = f.read().decode()
            return tail.strip().split()[-1]

    def record(self, *, case_id: str, task_id: str, event: str, details: str = ""):
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
        entry = {
            "case_id": case_id,
            "task_id": task_id,
            "event": event,
            "details": details,
            "ts": ts,
        }
        entry_json = json.dumps(entry, separators=(",", ":"))
        prev = self._last_hash()
        chain_hash = hashlib.sha256((prev + entry_json).encode()).hexdigest()
        line = f"{entry_json} {chain_hash}\n"
        with self.file.open("a", encoding="utf-8") as f:
            f.write(line)
