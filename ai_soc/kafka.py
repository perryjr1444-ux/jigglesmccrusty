from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Optional

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:  # pragma: no cover - optional dependency
    AIOKafkaConsumer = None
    AIOKafkaProducer = None

from .config import Settings
from .models import TelemetryEvent, ThreatIntelEvent
from .service import AISOCService

LOGGER = logging.getLogger(__name__)


class KafkaBridge:
    """Consumes telemetry/threat intel topics and forwards alerts."""

    def __init__(self, service: AISOCService, settings: Settings) -> None:
        self._service = service
        self._settings = settings
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if AIOKafkaConsumer is None or self._settings.kafka_bootstrap_servers is None:
            LOGGER.info("Kafka not configured; running in API-only mode")
            return
        LOGGER.info("Starting Kafka bridge on %s", self._settings.kafka_bootstrap_servers)
        self._consumer = AIOKafkaConsumer(
            self._settings.metrics_topic,
            self._settings.proposals_topic,
            self._settings.approvals_topic,
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            enable_auto_commit=True,
            auto_offset_reset="earliest",
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
        )
        await self._consumer.start()
        await self._producer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()

    async def _consume_loop(self) -> None:
        assert self._consumer is not None
        async for message in self._consumer:
            try:
                payload = json.loads(message.value.decode("utf-8"))
            except json.JSONDecodeError:
                LOGGER.warning("Discarding malformed message on %s", message.topic)
                continue
            if message.topic == self._settings.metrics_topic:
                await self._handle_telemetry(payload)
            elif message.topic == self._settings.proposals_topic:
                await self._handle_threat_intel(payload)
            elif message.topic == self._settings.approvals_topic:
                await self._handle_approval(payload)

    async def _handle_threat_intel(self, payload: dict) -> None:
        try:
            event = ThreatIntelEvent.model_validate(payload)
        except Exception:
            LOGGER.exception("Failed to parse threat intel event")
            return
        response = await self._service.ingest_threat_intel(event)
        if response:
            await self._publish_alert_response(response)

    async def _handle_telemetry(self, payload: dict) -> None:
        try:
            event = TelemetryEvent.model_validate(payload)
        except Exception:
            LOGGER.exception("Failed to parse telemetry event")
            return
        response = await self._service.ingest_telemetry(event)
        if response:
            await self._publish_alert_response(response)

    async def _handle_approval(self, payload: dict) -> None:
        LOGGER.info("Received human approval payload: %s", payload)

    async def _publish_alert_response(self, response) -> None:
        if self._producer is None:
            return
        await self._producer.send_and_wait(
            self._settings.alerts_topic,
            json.dumps(response.alert.model_dump(mode="json")).encode("utf-8"),
        )
        if response.quota_update is not None:
            await self._producer.send_and_wait(
                self._settings.quota_updates_topic,
                json.dumps(response.quota_update.model_dump(mode="json")).encode("utf-8"),
            )
