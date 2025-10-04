from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Settings:
    """Configuration for the AI SOC service."""

    kafka_bootstrap_servers: Optional[str] = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    )
    metrics_topic: str = field(default_factory=lambda: os.getenv("KAFKA_METRICS_TOPIC", "rbp.metrics"))
    proposals_topic: str = field(
        default_factory=lambda: os.getenv("KAFKA_PROPOSALS_TOPIC", "rbp.proposals")
    )
    approvals_topic: str = field(
        default_factory=lambda: os.getenv("KAFKA_APPROVALS_TOPIC", "rbp.approvals")
    )
    alerts_topic: str = field(default_factory=lambda: os.getenv("KAFKA_ALERTS_TOPIC", "rbp.alerts"))
    quota_updates_topic: str = field(
        default_factory=lambda: os.getenv("KAFKA_QUOTA_UPDATES_TOPIC", "rbp.quota_updates")
    )
    storage_path: Path = field(
        default_factory=lambda: Path(os.getenv("AI_SOC_STORAGE", "data/ai-soc-state.json"))
    )
    service_name: str = field(default_factory=lambda: os.getenv("AI_SOC_SERVICE_NAME", "ai-soc"))
    lumo_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("LUMO_ENDPOINT"))
    baseline_outbound_threshold: int = field(
        default_factory=lambda: int(os.getenv("BASELINE_OUTBOUND_THRESHOLD", "120"))
    )


DEFAULT_SETTINGS = Settings()
