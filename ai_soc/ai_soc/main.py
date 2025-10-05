"""FastAPI entrypoint for the AI SOC microservice."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .config import get_settings
from .models import EnrichedAlert, PaginatedAlerts, QuotaUpdate, TelemetryEvent
from .services.alerts import AlertOrchestrator
from .services.llm import RemediationClient
from .services.quota_manager import QuotaPublisher
from .services.storage import AlertStore
from .services.telemetry import InMemoryTelemetryBuffer, TelemetryStream

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    store = AlertStore()
    llm_client = RemediationClient(settings)
    orchestrator = AlertOrchestrator(store=store, llm=llm_client)
    telemetry_buffer = InMemoryTelemetryBuffer()
    quota_publisher = QuotaPublisher(settings)
    telemetry_stream = TelemetryStream(settings)

    app.state.settings = settings
    app.state.store = store
    app.state.llm = llm_client
    app.state.orchestrator = orchestrator
    app.state.telemetry_buffer = telemetry_buffer
    app.state.quota_publisher = quota_publisher
    app.state.telemetry_stream = telemetry_stream

    await quota_publisher.start()
    telemetry_task: asyncio.Task | None = None
    try:
        await telemetry_stream.start()
        telemetry_task = asyncio.create_task(
            _telemetry_loop(telemetry_stream, orchestrator, telemetry_buffer)
        )
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("telemetry.start_failed", error=str(exc))

    try:
        yield
    finally:
        if telemetry_task:
            telemetry_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await telemetry_task
        await llm_client.close()
        await quota_publisher.stop()
        await telemetry_stream.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="AI SOC", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    def _get_orchestrator() -> AlertOrchestrator:
        return app.state.orchestrator

    def _get_store() -> AlertStore:
        return app.state.store

    def _get_quota_publisher() -> QuotaPublisher:
        return app.state.quota_publisher

    @app.post("/telemetry", response_model=TelemetryEvent)
    async def ingest_telemetry(event: TelemetryEvent) -> TelemetryEvent:
        buffer: InMemoryTelemetryBuffer = app.state.telemetry_buffer
        buffer.append(event)
        orchestrator = _get_orchestrator()
        alert = orchestrator.correlate(event)
        if alert:
            await _handle_alert(orchestrator, _get_quota_publisher(), alert)
        return event

    @app.get("/alerts", response_model=PaginatedAlerts)
    async def list_alerts(
        limit: int = Query(default=20, ge=1, le=200), cursor: int | None = Query(default=None, ge=0)
    ) -> PaginatedAlerts:
        store = _get_store()
        return store.list(limit=limit, cursor=cursor)

    @app.get("/alerts/{alert_id}", response_model=EnrichedAlert)
    async def get_alert(alert_id: str) -> EnrichedAlert:
        alert = _get_store().get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @app.post("/alerts/{alert_id}/remediate")
    async def remediate_alert(alert_id: str) -> JSONResponse:
        orchestrator = _get_orchestrator()
        alert = orchestrator.get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        plan, quota_update = await _handle_alert(
            orchestrator, _get_quota_publisher(), alert
        )
        return JSONResponse(content=plan.model_dump(mode="json"))

    @app.post("/quota-updates", response_model=QuotaUpdate)
    async def emit_quota_update(update: QuotaUpdate) -> QuotaUpdate:
        await _get_quota_publisher().publish(update)
        return update

    return app


async def _telemetry_loop(
    stream: TelemetryStream,
    orchestrator: AlertOrchestrator,
    buffer: InMemoryTelemetryBuffer,
) -> None:
    """Coroutine that consumes telemetry and triggers alert workflows."""

    async for event in stream.stream():
        buffer.append(event)
        alert = orchestrator.correlate(event)
        if alert:
            # Remediate automatically during background processing. Quota
            # publishing is skipped because the background loop does not own
            # the publisher instance.
            await orchestrator.remediate(alert)


async def _handle_alert(
    orchestrator: AlertOrchestrator,
    quota_publisher: QuotaPublisher,
    alert: EnrichedAlert,
):
    plan = await orchestrator.remediate(alert)
    quota_update = orchestrator.derive_quota_update(plan)
    if quota_update:
        await quota_publisher.publish(quota_update)
    return plan, quota_update


app = create_app()

__all__ = ["create_app", "app"]
