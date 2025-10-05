"""Configuration helpers for the AI SOC service."""

from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    service_name: str = Field(default="ai-soc", description="Service identifier")
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", description="Kafka bootstrap server list"
    )
    kafka_group_id: str = Field(default="ai-soc", description="Kafka consumer group")
    telemetry_topics: List[str] = Field(
        default_factory=lambda: ["rbp.metrics", "rbp.proposals", "rbp.approvals"],
        description="Kafka topics to subscribe to for telemetry",
    )
    alerts_topic: str = Field(default="rbp.alerts", description="Topic for AI SOC alerts")
    quota_updates_topic: str = Field(
        default="rbp.quota_updates", description="Topic for quota manager updates"
    )
    threat_intel_feeds: List[AnyUrl] = Field(
        default_factory=lambda: [
            "https://feeds.cve.org/",
            "https://otx.alienvault.com/api/v1/indicators",
        ],
        description="Threat intelligence feed URLs",
    )
    llm_model: str = Field(
        default="lumo-ai-soc",
        description="Identifier for the LLM prompt profile used to build remediations",
    )
    llm_endpoint: AnyUrl | None = Field(
        default=None,
        description="Optional override for the LLM inference endpoint",
    )
    review_board_webhook: AnyUrl | None = Field(
        default=None, description="Optional webhook for notifying the review board"
    )

    model_config = SettingsConfigDict(env_prefix="AI_SOC_", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


__all__ = ["Settings", "get_settings"]
