"""FastAPI routes for the blue-team framework."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.orchestrator import Orchestrator
from core.models import Case, Task

router = APIRouter()

_orchestrator = Orchestrator()


class CaseRequest(BaseModel):
    title: str
    description: str
    playbook: str
    context: dict | None = None


class ApprovalRequest(BaseModel):
    task_id: str
    approver: str


@router.post("/cases", response_model=Case)
def ingest_case(payload: CaseRequest) -> Case:
    try:
        return _orchestrator.ingest_case(
            payload.title,
            payload.description,
            payload.playbook,
            payload.context or {},
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - bubbled to client
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/cases", response_model=list[Case])
def list_cases() -> list[Case]:
    return _orchestrator.list_cases()


@router.post("/cases/{case_id}/approve", response_model=Task)
def approve_task(case_id: str, payload: ApprovalRequest) -> Task:
    try:
        return _orchestrator.approve_task(case_id, payload.task_id, payload.approver)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/audit")
def read_audit() -> dict:
    return {
        "entries": _orchestrator.get_audit_log(),
    }
