"""Pydantic schemas for framework entities."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class CaseStatus(str, Enum):
    OPEN = "open"
    AWAITING_APPROVAL = "awaiting_approval"
    CLOSED = "closed"


class Artifact(BaseModel):
    id: str
    case_id: str
    task_id: str
    type: str
    content: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    id: str
    node_id: str
    name: str
    agent: str
    action: str
    status: TaskStatus = TaskStatus.PENDING
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    approvals: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Case(BaseModel):
    id: str
    title: str
    description: str
    playbook: str
    context: Dict[str, Any] = Field(default_factory=dict)
    status: CaseStatus = CaseStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tasks: List[Task] = Field(default_factory=list)


class AuditEntry(BaseModel):
    index: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    hash: str = ""
    parent_hash: Optional[str] = None


class PlaybookNode(BaseModel):
    id: str
    name: str
    description: Optional[str]
    agent: str
    action: str
    next: List[str] = Field(default_factory=list)
    requires_approval: bool = False


class Playbook(BaseModel):
    id: str
    name: str
    description: Optional[str]
    entry: str
    nodes: Dict[str, PlaybookNode]
