"""Lightweight wrapper for LLM-based remediation generation."""

from __future__ import annotations

from typing import Iterable, Sequence

import httpx

from ..config import Settings
from ..models import EnrichedAlert, RemediationAction, RemediationPlan


PROMPT_TEMPLATE = """You are the AI SOC remediation engine. Translate the following alert into concrete defensive actions.\n\nAlert Summary: {summary}\nSeverity: {severity}\nDetails: {details}\nIndicators: {indicators}\n\nReturn a JSON list of actions. Each action must contain type, payload (object), and rationale."""


class RemediationClient:
    """Create remediation plans from alerts using an external LLM."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, read=60.0))

    async def close(self) -> None:
        await self._client.aclose()

    async def build_plan(self, alert: EnrichedAlert) -> RemediationPlan:
        """Call the LLM endpoint (or fallback heuristic) to build a remediation plan."""

        if self._settings.llm_endpoint:
            payload = {
                "model": self._settings.llm_model,
                "prompt": PROMPT_TEMPLATE.format(
                    summary=alert.summary,
                    severity=alert.severity.value,
                    details=alert.details,
                    indicators=[e.payload.get("indicator") for e in alert.correlated_events],
                ),
            }
            response = await self._client.post(
                str(self._settings.llm_endpoint), json=payload
            )
            response.raise_for_status()
            data = response.json()
            actions_payload: Sequence[dict] = data.get("actions", [])
            actions = [RemediationAction.model_validate(item) for item in actions_payload]
        else:
            actions = self._fallback(alert)

        return RemediationPlan(
            alert_id=alert.id,
            actions=list(actions),
            model=self._settings.llm_model,
        )

    def _fallback(self, alert: EnrichedAlert) -> Iterable[RemediationAction]:
        """Generate deterministic remediation guidance without an external model."""

        base_payload = {
            "alert_id": alert.id,
            "severity": alert.severity.value,
        }
        actions = [
            RemediationAction(
                action_type="opa_policy",
                payload={
                    **base_payload,
                    "policy": {
                        "name": f"deny-{alert.id}",
                        "match": alert.details.get("match", {}),
                    },
                },
                rationale="Block suspicious activity via OPA until analyst review.",
            ),
            RemediationAction(
                action_type="network_policy",
                payload={
                    **base_payload,
                    "namespace": alert.details.get("namespace", "default"),
                    "isolation": True,
                },
                rationale="Isolate workload pending containment checks.",
            ),
        ]

        if alert.severity in {alert.severity.HIGH, alert.severity.CRITICAL}:  # type: ignore[attr-defined]
            actions.append(
                RemediationAction(
                    action_type="quota_update",
                    payload={
                        "agent_id": alert.details.get("agent_id"),
                        "enabled": False,
                    },
                    rationale="Disable self-suggest for the offending agent until remediated.",
                )
            )

        return actions


__all__ = ["RemediationClient"]
