# Core Data Contract Models

This document describes the core Pydantic models that define data contracts across the AI SOC system, including the API, orchestrator, and audit log.

## Overview

The core models provide:

- **Strong type safety** through comprehensive type annotations
- **Validation** of all input data with meaningful error messages
- **Immutability patterns** to prevent accidental mutations after persistence
- **Audit trails** through custody chains and status tracking
- **Lifecycle management** with explicit state transitions

## Models

### Case

Represents an investigation case that aggregates related tasks and artifacts.

**Key Features:**
- Unique case identifier (UUID)
- Status tracking (OPEN → IN_PROGRESS → RESOLVED → CLOSED)
- Priority levels (1-5, where 1 is highest)
- Aggregates tasks and artifacts by ID
- Automatic timestamp management

**Immutability:**
Core fields (case_id, title, created_at) are immutable after creation. Status, tasks, artifacts, and metadata can be updated through dedicated methods that return new instances.

**Example Usage:**

```python
from core.models import Case, CaseStatus

# Create a new case
case = Case(
    title="Suspicious Network Activity",
    description="Detected unusual outbound connections from endpoint",
    priority=2,
    assignee="security-team"
)

# Add tasks and artifacts
case_v2 = case.add_task("task-123")
case_v3 = case_v2.add_artifact("artifact-456")

# Update status
case_v4 = case_v3.update_status(CaseStatus.IN_PROGRESS)

# Close case
case_closed = case_v4.update_status(CaseStatus.CLOSED)
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | str | No (auto-generated) | Unique identifier |
| `title` | str | Yes | Human-readable case title |
| `description` | str | No (default: "") | Detailed description |
| `status` | CaseStatus | No (default: OPEN) | Current status |
| `priority` | int | No (default: 3) | Priority level (1-5) |
| `assignee` | str | No | User or team assigned |
| `tasks` | List[str] | No (default: []) | Associated task IDs |
| `artifacts` | List[str] | No (default: []) | Associated artifact IDs |
| `created_at` | datetime | No (auto-generated) | Creation timestamp |
| `updated_at` | datetime | No (auto-generated) | Last update timestamp |
| `closed_at` | datetime | No | Case closure timestamp |
| `metadata` | Dict[str, Any] | No (default: {}) | Additional metadata |

**Status Enum:**
- `OPEN` - Case created, not yet assigned or started
- `IN_PROGRESS` - Active investigation underway
- `RESOLVED` - Investigation complete, awaiting closure
- `CLOSED` - Case finalized and archived

---

### Task

Represents a unit of work executed by connectors in the orchestration system.

**Key Features:**
- Unique task identifier (UUID)
- Status lifecycle (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED)
- Timestamp tracking (created, started, completed)
- Input payload and output result storage
- Error tracking for failed tasks

**Immutability:**
Core fields (task_id, case_id, task_type, connector, payload, created_at) are immutable after creation. Status, output, and error_message can be updated through dedicated state transition methods.

**Example Usage:**

```python
from core.models import Task, TaskStatus

# Create a new task
task = Task(
    case_id="case-789",
    task_type="take_snapshot",
    connector="evidence",
    payload={
        "local_path": "/var/log/system.log",
        "kind": "log"
    }
)

# Mark as running
task_running = task.mark_running()

# Complete with output
task_completed = task_running.mark_completed({
    "artifact_id": "artifact-123",
    "s3_path": "s3://evidence/case-789/system.log"
})

# Or mark as failed
# task_failed = task_running.mark_failed("Connection timeout")
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | str | No (auto-generated) | Unique identifier |
| `case_id` | str | Yes | Associated case ID |
| `task_type` | str | Yes | Type of task (e.g., take_snapshot) |
| `connector` | str | Yes | Connector responsible for execution |
| `payload` | Dict[str, Any] | No (default: {}) | Input parameters |
| `status` | TaskStatus | No (default: PENDING) | Current status |
| `output` | Dict[str, Any] | No | Result data |
| `error_message` | str | No | Error message if failed |
| `created_at` | datetime | No (auto-generated) | Creation timestamp |
| `started_at` | datetime | No | Execution start timestamp |
| `completed_at` | datetime | No | Completion timestamp |
| `metadata` | Dict[str, Any] | No (default: {}) | Additional metadata |

**Status Enum:**
- `PENDING` - Task created, awaiting execution
- `RUNNING` - Task currently executing
- `COMPLETED` - Task finished successfully
- `FAILED` - Task failed with error
- `CANCELLED` - Task cancelled before completion

**State Transition Rules:**
- `mark_running()`: PENDING → RUNNING
- `mark_completed(output)`: RUNNING → COMPLETED
- `mark_failed(error)`: PENDING/RUNNING → FAILED

---

### Artifact

Represents immutable evidence metadata for files, logs, or data captured during investigations.

**Key Features:**
- Unique artifact identifier (UUID)
- SHA-256 hash for content integrity
- S3 storage path
- Redaction map for PII/sensitive data
- Chain of custody tracking
- Content validation

**Immutability:**
All core fields (artifact_id, case_id, kind, sha256, s3_path, created_at) are immutable after creation. Only redaction_map and custody_chain can be updated through dedicated methods.

**Example Usage:**

```python
from core.models import Artifact
import uuid

# Create an artifact
artifact = Artifact(
    case_id="case-123",
    kind="log",
    sha256="a1b2c3d4..." * 8,  # 64-char hex string
    s3_path="s3://evidence/case-123/system.log"
)

# Add custody entry
artifact_v2 = artifact.add_custody_entry(
    actor="EvidenceClerk",
    action="create",
    details={"method": "automated_capture"}
)

# Add another custody entry
artifact_v3 = artifact_v2.add_custody_entry(
    actor="Analyst",
    action="review",
    details={"reviewer": "alice@example.com"}
)
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact_id` | UUID | No (auto-generated) | Unique identifier |
| `case_id` | str | Yes | Associated case ID |
| `kind` | str | Yes | Type (log, screenshot, memory_dump, etc.) |
| `sha256` | str | Yes | SHA-256 hash (64 hex chars) |
| `s3_path` | str | Yes | S3 URI (must start with s3://) |
| `redaction_map` | Dict[str, str] | No (default: {}) | Original → Redacted mappings |
| `custody_chain` | List[CustodyEntry] | No (default: []) | Chain of custody |
| `created_at` | datetime | No (auto-generated) | Creation timestamp |
| `metadata` | Dict[str, Any] | No (default: {}) | Additional metadata |

**Validation Rules:**
- SHA-256 must be exactly 64 hexadecimal characters (normalized to lowercase)
- S3 path must start with `s3://`
- Custody entries are frozen after creation

---

### CustodyEntry

Represents a single entry in an artifact's chain of custody.

**Key Features:**
- Immutable after creation (frozen model)
- Automatic timestamp generation
- Records actor, action, and details

**Example Usage:**

```python
from core.models import CustodyEntry

entry = CustodyEntry(
    actor="SecurityAnalyst",
    action="transfer",
    details={
        "from": "evidence_vault",
        "to": "legal_review",
        "reason": "subpoena_compliance"
    }
)
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actor` | str | Yes | Identity performing the action |
| `action` | str | Yes | Action performed (create, update, transfer, etc.) |
| `timestamp` | datetime | No (auto-generated) | When action occurred |
| `details` | Dict[str, Any] | No (default: {}) | Additional context |

---

## Design Principles

### 1. Immutability Through Copy-on-Write

Models use Pydantic's `model_copy()` to create new instances when modifications are needed. This ensures:

- Original instances remain unchanged
- Changes are explicit and traceable
- Concurrent access is safe
- History can be maintained

```python
# Bad: Direct mutation (won't work, raises error)
# case.status = CaseStatus.CLOSED

# Good: Explicit copy with updates
case_closed = case.update_status(CaseStatus.CLOSED)
```

### 2. Validation at Construction

All validation happens when the model is constructed, ensuring:

- Invalid data is rejected early
- Error messages are clear and actionable
- Runtime errors are minimized

```python
# Validation errors raised immediately
try:
    artifact = Artifact(
        case_id="case-123",
        kind="log",
        sha256="invalid",  # Too short
        s3_path="/local/path"  # Wrong format
    )
except ValidationError as e:
    print(e)  # Clear error messages
```

### 3. Type Safety

Comprehensive type annotations enable:

- IDE autocomplete and hints
- Static type checking with mypy
- Better documentation
- Fewer runtime errors

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Full IDE support
    case: Case = Case(title="Test")
    task_id: str = case.tasks[0]  # Type-checked
```

### 4. State Transition Safety

Explicit methods for state transitions prevent invalid states:

```python
# Only valid transitions allowed
task = Task(...)  # PENDING
task_running = task.mark_running()  # OK: PENDING → RUNNING
task_completed = task_running.mark_completed({"result": "success"})  # OK

# Invalid transitions raise errors
task.mark_completed({"result": "success"})  # Error: can't complete pending task
```

---

## Integration with Existing Code

### Evidence Connector

The Evidence Connector uses the Artifact model:

```python
from core.models import Artifact
import uuid
import datetime

# Create artifact in connector
artifact = Artifact(
    artifact_id=uuid.uuid4(),
    case_id=case_id,
    kind=kind,
    sha256=file_hash,
    s3_path=f"s3://evidence/{key}",
    redaction_map={},
    custody_chain=[
        {"actor": "EvidenceClerk", "action": "create", "ts": datetime.datetime.utcnow()}
    ],
)

# Return serialized
return {"artifact": artifact.model_dump(), "summary": f"Captured {kind} → {key}"}
```

### Audit Log

The Audit Log references case_id and task_id:

```python
from core.audit import AuditLog

audit = AuditLog(case_id=case.case_id)
audit.record(
    case_id=case.case_id,
    task_id=task.task_id,
    event="task_completed",
    details=f"Task {task.task_type} completed successfully"
)
```

### Orchestrator

The orchestrator uses Task models for execution:

```python
from core.models import Task, TaskStatus

# Create task
task = Task(
    case_id="case-123",
    task_type="enrich_alert",
    connector="llm",
    payload={"alert_id": "alert-456"}
)

# Execute
task_running = task.mark_running()
try:
    result = await connector.execute(task_running.payload)
    task_completed = task_running.mark_completed(result)
except Exception as e:
    task_failed = task_running.mark_failed(str(e))
```

---

## Testing

Comprehensive test coverage is provided in `tests/test_core_models.py`:

- Schema validation tests
- Immutability enforcement tests
- State transition tests
- Custody chain tests
- Edge case handling
- Serialization/deserialization tests

Run tests:

```bash
python -m pytest tests/test_core_models.py -v
```

---

## Migration Guide

If you have existing code using the old Artifact model:

### Before:
```python
artifact = Artifact(
    artifact_id=uuid.uuid4(),
    case_id="case-123",
    kind="log",
    sha256=file_hash,
    s3_path=s3_uri,
    redaction_map={},
    custody_chain=[{"actor": "Agent", "action": "create", "ts": datetime.utcnow()}]
)
```

### After:
The same code works! But custody_chain entries should use CustodyEntry:

```python
from core.models import Artifact, CustodyEntry

artifact = Artifact(
    artifact_id=uuid.uuid4(),
    case_id="case-123",
    kind="log",
    sha256=file_hash,
    s3_path=s3_uri,
    redaction_map={},
    custody_chain=[
        CustodyEntry(actor="Agent", action="create")
    ]
)

# Or use the helper method:
artifact = Artifact(
    case_id="case-123",
    kind="log",
    sha256=file_hash,
    s3_path=s3_uri,
)
artifact = artifact.add_custody_entry("Agent", "create")
```

---

## Future Enhancements

Potential improvements for future iterations:

1. **Relationship tracking** - Direct object references instead of ID strings
2. **Event sourcing** - Track all mutations as events
3. **Computed fields** - Derived metrics (e.g., task duration, case age)
4. **Custom validators** - Domain-specific validation rules
5. **Versioning** - Schema version tracking for migrations
6. **Encryption** - Automatic field-level encryption for sensitive data

---

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Chain of Custody Best Practices](https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-tool-testing-program-cftt)
