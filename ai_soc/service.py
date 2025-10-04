from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from .config import Settings
from .llm import LumoClient
from .models import (
    Alert,
    AlertAcknowledgement,
    AlertResponse,
    AlertStatus,
    QuotaUpdate,
    RemediationAction,
    Severity,
    TelemetryEvent,
    ThreatIntelEvent,
)
from .storage import AISOCStorage

LOGGER = logging.getLogger(__name__)


class AISOCService:
    """Coordinates threat ingestion, detection, and response."""

    def __init__(self, settings: Settings, storage: AISOCStorage, llm: LumoClient) -> None:
        self._settings = settings
        self._storage = storage
        self._llm = llm
        self._lock = asyncio.Lock()

    async def ingest_threat_intel(self, event: ThreatIntelEvent) -> AlertResponse | None:
        LOGGER.info("Ingesting threat intel %s from %s", event.indicator, event.source)
        if event.severity in {Severity.high, Severity.critical}:
            alert = await self._create_alert(
                source="threat-intel",
                title=f"New high-severity indicator {event.indicator}",
                description=event.summary,
                severity=event.severity,
                context={"indicator": event.indicator, "source": event.source},
            )
            return await self._enrich_alert(alert)
        return None

    async def ingest_telemetry(self, event: TelemetryEvent) -> AlertResponse | None:
        LOGGER.debug("Processing telemetry for device %s", event.device_id)
        outbound = int(event.signals.get("outbound_connections", 0))
        if outbound > self._settings.baseline_outbound_threshold:
            alert = await self._create_alert(
                source="telemetry",
                title="Outbound connection spike",
                description=(
                    f"Device {event.device_id} exceeded outbound threshold "
                    f"({outbound}>{self._settings.baseline_outbound_threshold})"
                ),
                severity=Severity.high,
                context={
                    "device_id": event.device_id,
                    "agent_id": event.agent_id,
                    "outbound_connections": outbound,
                },
            )
            return await self._enrich_alert(alert)
        return None

    async def acknowledge_alert(self, alert_id: str, payload: AlertAcknowledgement) -> Alert | None:
        alert = self._storage.get_alert(alert_id)
        if alert is None:
            return None
        LOGGER.info("Alert %s acknowledged by %s", alert_id, payload.analyst)
        alert.status = AlertStatus.acknowledged
        alert.context.setdefault("acknowledgements", []).append(
            {"analyst": payload.analyst, "message": payload.message, "timestamp": datetime.utcnow().isoformat()}
        )
        self._storage.upsert_alert(alert)
        return alert

    def list_alerts(self) -> List[Alert]:
        return self._storage.list_alerts()

    def get_alert(self, alert_id: str) -> Alert | None:
        return self._storage.get_alert(alert_id)

    def list_remediations(self) -> List[RemediationAction]:
        return self._storage.list_remediations()

    def list_quota_updates(self) -> List[QuotaUpdate]:
        return self._storage.list_quota_updates()

    async def _create_alert(
        self,
        *,
        source: str,
        title: str,
        description: str,
        severity: Severity,
        context: Optional[dict] = None,
    ) -> Alert:
        async with self._lock:
            alert = Alert(
                id=str(uuid4()),
                created_at=datetime.utcnow(),
                source=source,
                title=title,
                description=description,
                severity=severity,
                context=context or {},
            )
            self._storage.upsert_alert(alert)
            return alert

    async def _enrich_alert(self, alert: Alert) -> AlertResponse:
        remediation = await self._llm.generate_remediation(alert)
        self._storage.upsert_remediation(remediation)
        quota_update = None
        if remediation.quota_update and alert.context.get("agent_id"):
            quota_update = QuotaUpdate(
                id=str(uuid4()),
                agent_id=alert.context["agent_id"],
                enforced_at=datetime.utcnow(),
                reason=alert.description,
                self_suggest_enabled=False,
            )
            self._storage.upsert_quota_update(quota_update)
        LOGGER.debug("Generated remediation %s for alert %s", remediation.id, alert.id)
        return AlertResponse(alert=alert, remediation=remediation, quota_update=quota_update)
