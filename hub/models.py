from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Team(str, Enum):
    red = "red"
    blue = "blue"
    purple = "purple"


class TaskStatus(str, Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"


class TaskCreate(BaseModel):
    team: Team
    type: str = Field(..., description="Task type identifier")
    payload: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    result: Dict[str, Any]


class Task(BaseModel):
    id: str
    team: Team
    type: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.queued
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = None

    def with_status(self, status: TaskStatus) -> "Task":
        self.status = status
        self.updated_at = datetime.utcnow()
        return self

    def with_result(self, result: Dict[str, Any]) -> "Task":
        self.result = result
        self.status = TaskStatus.completed
        self.updated_at = datetime.utcnow()
        return self


class TaskEnvelope(BaseModel):
    task: Task
    queue_position: int
