from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict, List

from .models import Alert, QuotaUpdate, RemediationAction


class AISOCStorage:
    """JSON storage backend for alerts and responses."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"alerts": {}, "remediations": {}, "quota_updates": {}})

    def _read(self) -> Dict:
        with self._path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, payload: Dict) -> None:
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def upsert_alert(self, alert: Alert) -> None:
        with self._lock:
            data = self._read()
            data.setdefault("alerts", {})[alert.id] = alert.model_dump(mode="json")
            self._write(data)

    def upsert_remediation(self, remediation: RemediationAction) -> None:
        with self._lock:
            data = self._read()
            data.setdefault("remediations", {})[remediation.id] = remediation.model_dump(mode="json")
            self._write(data)

    def upsert_quota_update(self, update: QuotaUpdate) -> None:
        with self._lock:
            data = self._read()
            data.setdefault("quota_updates", {})[update.id] = update.model_dump(mode="json")
            self._write(data)

    def list_alerts(self) -> List[Alert]:
        with self._lock:
            data = self._read()
        alerts = data.get("alerts", {})
        return [Alert.model_validate(payload) for payload in alerts.values()]

    def get_alert(self, alert_id: str) -> Alert | None:
        with self._lock:
            data = self._read()
        payload = data.get("alerts", {}).get(alert_id)
        if payload is None:
            return None
        return Alert.model_validate(payload)

    def list_remediations(self) -> List[RemediationAction]:
        with self._lock:
            data = self._read()
        remediations = data.get("remediations", {})
        return [RemediationAction.model_validate(payload) for payload in remediations.values()]

    def list_quota_updates(self) -> List[QuotaUpdate]:
        with self._lock:
            data = self._read()
        updates = data.get("quota_updates", {})
        return [QuotaUpdate.model_validate(payload) for payload in updates.values()]
