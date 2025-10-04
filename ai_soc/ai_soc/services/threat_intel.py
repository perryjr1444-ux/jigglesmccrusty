"""Threat intelligence ingestion."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable, List

import httpx
import structlog

from ..config import Settings
from ..models import ThreatIntelRecord

logger = structlog.get_logger(__name__)


class ThreatIntelFetcher:
    """Periodic task that downloads indicators from configured feeds."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(15.0, read=30.0))
        self._cache: dict[str, datetime] = {}
        self._running = False

    async def run(self, interval_seconds: int = 900) -> Iterable[ThreatIntelRecord]:
        """Continuously fetch threat intel, yielding new records."""

        self._running = True
        while self._running:
            results: List[ThreatIntelRecord] = []
            for feed in self._settings.threat_intel_feeds:
                try:
                    payload = await self._client.get(str(feed))
                    payload.raise_for_status()
                except httpx.HTTPError as exc:  # pragma: no cover - best effort
                    logger.warning("threat_intel.fetch_failed", feed=str(feed), error=str(exc))
                    continue

                updated = payload.headers.get("last-modified")
                if updated and updated == self._cache.get(str(feed)):
                    continue

                indicators = self._parse_feed(payload.text, source=str(feed))
                results.extend(indicators)
                if updated:
                    self._cache[str(feed)] = updated

            for record in results:
                yield record

            await asyncio.sleep(interval_seconds)

    async def close(self) -> None:
        self._running = False
        await self._client.aclose()

    def _parse_feed(self, raw: str, source: str) -> List[ThreatIntelRecord]:
        """Parse feed payloads into standardised records."""

        records: List[ThreatIntelRecord] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            indicator, _, description = line.partition(",")
            records.append(
                ThreatIntelRecord(
                    source=source,
                    indicator=indicator.strip(),
                    description=description.strip() or None,
                    tags=["feed"],
                )
            )
        return records


__all__ = ["ThreatIntelFetcher"]
