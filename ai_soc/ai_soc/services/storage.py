"""In-memory persistence used by the demo implementation."""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterable, Optional

from ..models import EnrichedAlert, PaginatedAlerts


class AlertStore:
    """Store enriched alerts for later retrieval via the API."""

    def __init__(self, capacity: int = 1000) -> None:
        self._alerts: Deque[EnrichedAlert] = deque(maxlen=capacity)

    def add(self, alert: EnrichedAlert) -> None:
        self._alerts.append(alert)

    def list(self, limit: int = 50, cursor: Optional[int] = None) -> PaginatedAlerts:
        items = list(self._alerts)
        start = cursor or 0
        end = min(start + limit, len(items))
        next_cursor = str(end) if end < len(items) else None
        return PaginatedAlerts(alerts=list(items[start:end]), next_page=next_cursor)

    def get(self, alert_id: str) -> EnrichedAlert | None:
        for alert in self._alerts:
            if alert.id == alert_id:
                return alert
        return None

    def all(self) -> Iterable[EnrichedAlert]:
        return list(self._alerts)


__all__ = ["AlertStore"]
