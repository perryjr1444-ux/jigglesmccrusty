from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class ThreatIntelEvent(BaseModel):
    source: str
    indicator: str = Field(..., description="CVE or threat identifier")
    summary: str
    severity: Severity = Severity.medium
    affected_products: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TelemetryEvent(BaseModel):
    device_id: str
    timestamp: datetime
    signals: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None


class Alert(BaseModel):
    id: str
    created_at: datetime
    source: str
    title: str
    description: str
    severity: Severity
    status: AlertStatus = AlertStatus.open
    context: Dict[str, Any] = Field(default_factory=dict)


class RemediationAction(BaseModel):
    id: str
    alert_id: str
    created_at: datetime
    actions: List[str]
    policy_patch: Optional[Dict[str, Any]] = None
    quota_update: Optional[Dict[str, Any]] = None


class QuotaUpdate(BaseModel):
    id: str
    agent_id: str
    enforced_at: datetime
    reason: str
    self_suggest_enabled: bool


class AlertResponse(BaseModel):
    alert: Alert
    remediation: Optional[RemediationAction] = None
    quota_update: Optional[QuotaUpdate] = None


class AlertAcknowledgement(BaseModel):
    analyst: str
    message: Optional[str] = None
