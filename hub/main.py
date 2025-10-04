from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .models import Task, TaskCreate, TaskEnvelope, TaskResult, Team
from .orchestrator import Orchestrator
from .storage import TaskStorage

app = FastAPI(title="LLM SOC Orchestration Hub", version="0.1.0")


def get_orchestrator() -> Orchestrator:
    storage_path = Path("data/task-store.json")
    if not hasattr(app.state, "orchestrator"):
        app.state.orchestrator = Orchestrator(TaskStorage(storage_path))
    return app.state.orchestrator  # type: ignore[attr-defined]


@app.post("/tasks", response_model=Task)
async def create_task(payload: TaskCreate, orchestrator: Orchestrator = Depends(get_orchestrator)) -> Task:
    return await orchestrator.create_task(payload)


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: str, orchestrator: Orchestrator = Depends(get_orchestrator)) -> Task:
    task = orchestrator.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/tasks", response_model=Dict[str, Task])
async def list_tasks(orchestrator: Orchestrator = Depends(get_orchestrator)) -> Dict[str, Task]:
    return orchestrator.list_tasks()


@app.post("/tasks/{task_id}/result", response_model=Task)
async def submit_result(
    task_id: str,
    payload: TaskResult,
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> Task:
    task = await orchestrator.acknowledge(task_id, payload.result)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/{task_id}/release", response_model=Task)
async def release_task(task_id: str, orchestrator: Orchestrator = Depends(get_orchestrator)) -> Task:
    task = await orchestrator.release(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/queue/next", response_model=Optional[TaskEnvelope])
async def next_task(
    team: Team = Query(..., description="Team queue to consume from"),
    wait: bool = Query(False, description="Long poll until a task is available"),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> Optional[TaskEnvelope]:
    envelope = await orchestrator.next_task(team=team, wait=wait)
    if envelope is None:
        return None
    return envelope


@app.get("/healthz")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})
