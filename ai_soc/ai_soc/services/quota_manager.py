"""Quota manager publisher."""

from __future__ import annotations

import json

from aiokafka import AIOKafkaProducer

from ..config import Settings
from ..models import QuotaUpdate


class QuotaPublisher:
    """Send quota updates to Kafka for downstream enforcement."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._producer: AIOKafkaProducer | None = None
        self._enabled = False

    async def start(self) -> None:
        if self._producer is not None:
            return
        producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        try:
            await producer.start()
        except Exception:  # pragma: no cover - optional dependency
            await producer.stop()
            self._producer = None
            self._enabled = False
            return
        self._producer = producer
        self._enabled = True

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
        self._enabled = False

    async def publish(self, update: QuotaUpdate) -> None:
        payload = update.model_dump()
        if self._enabled and self._producer is not None:
            await self._producer.send_and_wait(
                self._settings.quota_updates_topic, payload
            )


__all__ = ["QuotaPublisher"]
