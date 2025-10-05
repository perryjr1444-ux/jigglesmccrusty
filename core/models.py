import uuid
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Status of a task in the execution workflow."""
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """Represents a single task in a playbook execution."""
    task_id: str
    case_id: str
    playbook_id: str
    task_name: str
    task_type: str
    inputs: Dict[str, Any]
    needs: List[str]  # Task dependencies
    approval_required: bool
    idempotency_key: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approved_by: Optional[str] = None
    executed_at: Optional[str] = None


class Artifact(BaseModel):
    artifact_id: uuid.UUID
    case_id: str
    kind: str
    sha256: str
    s3_path: str
    redaction_map: Dict[str, str]
    custody_chain: List[Dict[str, Any]]
