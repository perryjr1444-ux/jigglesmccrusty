"""Telemetry ingestion utilities."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Callable, Iterable

from aiokafka import AIOKafkaConsumer

from ..config import Settings
from ..models import TelemetryEvent


class TelemetryStream:
    """Consume telemetry events from Kafka and expose them to the application."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        """Start the Kafka consumer."""

        if self._consumer is not None:
            return
        self._consumer = AIOKafkaConsumer(
            *self._settings.telemetry_topics,
            bootstrap_servers=self._settings.kafka_bootstrap_servers,
            group_id=self._settings.kafka_group_id,
            enable_auto_commit=True,
            value_deserializer=lambda m: TelemetryEvent.model_validate_json(m),
        )
        await self._consumer.start()

    async def stop(self) -> None:
        """Close the Kafka consumer."""

        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

    async def stream(self) -> AsyncIterator[TelemetryEvent]:
        """Yield telemetry events as they arrive."""

        if self._consumer is None:
            raise RuntimeError("TelemetryStream must be started before streaming")

        try:
            async for message in self._consumer:
                yield message.value
        except asyncio.CancelledError:
            raise

    async def pump(self, handler: Callable[[TelemetryEvent], None]) -> None:
        """Continuously dispatch telemetry events to a handler callable."""

        async for event in self.stream():
            handler(event)


class InMemoryTelemetryBuffer:
    """Simple in-memory buffer for telemetry events (used for tests and demos)."""

    def __init__(self, max_events: int = 1000) -> None:
        self._events: list[TelemetryEvent] = []
        self._max_events = max_events

    def append(self, event: TelemetryEvent) -> None:
        """Store an event, trimming the buffer if required."""

        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)

    def list(self) -> Iterable[TelemetryEvent]:
        """Return buffered telemetry events."""

        return list(self._events)


__all__ = ["TelemetryStream", "InMemoryTelemetryBuffer"]
