"""Alert enrichment and remediation orchestration."""

from __future__ import annotations

from typing import Iterable, Optional

import structlog

from ..models import EnrichedAlert, QuotaUpdate, RemediationPlan, Severity, TelemetryEvent
from .llm import RemediationClient
from .storage import AlertStore

logger = structlog.get_logger(__name__)


class AlertOrchestrator:
    """Coordinates telemetry correlation, LLM remediation, and quota updates."""

    def __init__(self, store: AlertStore, llm: RemediationClient) -> None:
        self._store = store
        self._llm = llm

    def correlate(self, event: TelemetryEvent) -> Optional[EnrichedAlert]:
        """Convert telemetry events into enriched alerts if heuristics match."""

        indicator = event.payload.get("indicator")
        if indicator:
            alert = EnrichedAlert(
                id=f"alert-{event.captured_at.timestamp()}-{event.source}",
                severity=Severity.HIGH if event.payload.get("severity") == "high" else Severity.MEDIUM,
                summary=f"Suspicious activity detected from {event.source}",
                details={
                    "match": {"indicator": indicator},
                    "agent_id": event.payload.get("agent_id"),
                    "namespace": event.payload.get("namespace", "default"),
                },
                correlated_events=[event],
                recommendations=["Review suggested remediations"],
            )
            self._store.add(alert)
            logger.info("alerts.correlated", alert_id=alert.id)
            return alert
        return None

    async def remediate(self, alert: EnrichedAlert) -> RemediationPlan:
        """Generate a remediation plan via the LLM service."""

        plan = await self._llm.build_plan(alert)
        logger.info("alerts.remediation_generated", alert_id=alert.id)
        return plan

    def derive_quota_update(self, plan: RemediationPlan) -> Optional[QuotaUpdate]:
        """Inspect the remediation plan for quota updates."""

        for action in plan.actions:
            if action.action_type == "quota_update":
                payload = action.payload
                if payload.get("agent_id"):
                    return QuotaUpdate(
                        agent_id=payload["agent_id"],
                        enabled=payload.get("enabled", False),
                        reason=action.rationale,
                    )
        return None

    def list_alerts(self, limit: int = 50, cursor: Optional[int] = None) -> Iterable[EnrichedAlert]:
        return self._store.list(limit=limit, cursor=cursor).alerts

    def get_alert(self, alert_id: str) -> Optional[EnrichedAlert]:
        return self._store.get(alert_id)


__all__ = ["AlertOrchestrator"]
