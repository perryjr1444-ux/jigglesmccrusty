from __future__ import annotations

import logging
from typing import Dict, List

from .models import Alert, RemediationAction

LOGGER = logging.getLogger(__name__)


class LumoClient:
    """Lightweight wrapper around the Lumo API (simulated)."""

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint

    async def generate_remediation(self, alert: Alert) -> RemediationAction:
        """Generate a remediation plan for a given alert."""

        LOGGER.debug("Generating remediation for alert %s", alert.id)
        actions: List[str] = [
            f"Review telemetry for device {alert.context.get('device_id', 'unknown')}",
            "Validate network isolation policy",
        ]
        policy_patch: Dict[str, str] = {
            "apiVersion": "opa/v1",
            "kind": "Policy",
            "metadata": {"name": f"auto-{alert.id}"},
            "spec": {
                "description": alert.title,
                "rule": "deny if outbound_connections > threshold",
            },
        }
        quota_update = None
        if alert.context.get("agent_id"):
            quota_update = {
                "agent_id": alert.context["agent_id"],
                "action": "disable_self_suggest",
                "reason": alert.description,
            }

        remediation = RemediationAction(
            id=f"rem-{alert.id}",
            alert_id=alert.id,
            created_at=alert.created_at,
            actions=actions,
            policy_patch=policy_patch,
            quota_update=quota_update,
        )
        return remediation
