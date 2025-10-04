"""Pydantic models shared across the AI SOC service."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Severity(str, Enum):
    """Standard severity levels for detections."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TelemetryEvent(BaseModel):
    """Represents raw telemetry emitted by agents or devices."""

    source: str = Field(..., description="Logical origin of the telemetry event")
    event_type: str = Field(..., description="Type of telemetry event")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Original payload for downstream enrichment"
    )
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Collection timestamp",
    )


class ThreatIntelRecord(BaseModel):
    """Normalised representation of an external threat intel indicator."""

    source: HttpUrl
    indicator: str
    description: str | None = None
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: List[str] = Field(default_factory=list)


class EnrichedAlert(BaseModel):
    """Alert that has been enriched by the AI SOC pipeline."""

    id: str = Field(..., description="Unique identifier for the alert")
    severity: Severity = Field(default=Severity.MEDIUM)
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlated_events: List[TelemetryEvent] = Field(default_factory=list)


class RemediationAction(BaseModel):
    """Machine-readable remediation output from the LLM."""

    action_type: str = Field(..., description="Type of remediation artifact")
    payload: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="", description="Narrative explaining the action")


class RemediationPlan(BaseModel):
    """LLM-generated remediation plan for an alert."""

    alert_id: str
    actions: List[RemediationAction]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model: str


class QuotaUpdate(BaseModel):
    """Instruction for the quota manager to toggle agent permissions."""

    agent_id: str
    enabled: bool
    reason: str
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaginatedAlerts(BaseModel):
    """Paginated response for alert listings."""

    alerts: List[EnrichedAlert]
    next_page: Optional[str] = None


__all__ = [
    "Severity",
    "TelemetryEvent",
    "ThreatIntelRecord",
    "EnrichedAlert",
    "RemediationPlan",
    "RemediationAction",
    "QuotaUpdate",
    "PaginatedAlerts",
]
