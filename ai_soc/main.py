from __future__ import annotations

import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException

from .config import DEFAULT_SETTINGS, Settings
from .kafka import KafkaBridge
from .llm import LumoClient
from .models import Alert, AlertAcknowledgement, AlertResponse, TelemetryEvent, ThreatIntelEvent
from .service import AISOCService
from .storage import AISOCStorage

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI SOC Service", version="0.1.0")


def get_settings() -> Settings:
    return DEFAULT_SETTINGS


def get_service(settings: Settings = Depends(get_settings)) -> AISOCService:
    if not hasattr(app.state, "service"):
        storage = AISOCStorage(settings.storage_path)
        llm = LumoClient(settings.lumo_endpoint)
        app.state.service = AISOCService(settings, storage, llm)
    return app.state.service  # type: ignore[attr-defined]


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    service = get_service(settings)
    bridge = KafkaBridge(service, settings)
    app.state.bridge = bridge
    await bridge.start()
    LOGGER.info("AI SOC service started")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    bridge: KafkaBridge | None = getattr(app.state, "bridge", None)
    if bridge is not None:
        await bridge.stop()
    LOGGER.info("AI SOC service stopped")


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.post("/threat-intel", response_model=AlertResponse | None)
async def ingest_threat_intel(
    payload: ThreatIntelEvent, service: AISOCService = Depends(get_service)
) -> AlertResponse | None:
    return await service.ingest_threat_intel(payload)


@app.post("/telemetry", response_model=AlertResponse | None)
async def ingest_telemetry(payload: TelemetryEvent, service: AISOCService = Depends(get_service)) -> AlertResponse | None:
    return await service.ingest_telemetry(payload)


@app.get("/alerts", response_model=List[Alert])
async def list_alerts(service: AISOCService = Depends(get_service)) -> List[Alert]:
    return service.list_alerts()


@app.get("/alerts/{alert_id}", response_model=Alert)
async def read_alert(alert_id: str, service: AISOCService = Depends(get_service)) -> Alert:
    alert = service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.post("/alerts/{alert_id}/ack", response_model=Alert)
async def acknowledge_alert(
    alert_id: str,
    payload: AlertAcknowledgement,
    service: AISOCService = Depends(get_service),
) -> Alert:
    alert = await service.acknowledge_alert(alert_id, payload)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.get("/remediations")
async def list_remediations(service: AISOCService = Depends(get_service)):
    return service.list_remediations()


@app.get("/quota-updates")
async def list_quota_updates(service: AISOCService = Depends(get_service)):
    return service.list_quota_updates()
