"""Comprehensive unit tests for core data contract models.

Tests cover:
- Schema validation and type constraints
- Immutability enforcement (fields cannot be directly mutated)
- State transitions and lifecycle methods
- Custody chain and audit trail functionality
- Edge cases and validation rules
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from core.models import (
    Artifact,
    Case,
    CaseStatus,
    CustodyEntry,
    Task,
    TaskStatus,
)


class TestCustodyEntry:
    """Tests for the CustodyEntry model."""

    def test_custody_entry_creation(self):
        """Test basic custody entry creation with all fields."""
        entry = CustodyEntry(
            actor="TestAgent",
            action="create",
            details={"reason": "initial capture"},
        )
        assert entry.actor == "TestAgent"
        assert entry.action == "create"
        assert isinstance(entry.timestamp, datetime)
        assert entry.details == {"reason": "initial capture"}

    def test_custody_entry_defaults(self):
        """Test custody entry with default values."""
        entry = CustodyEntry(actor="Agent", action="transfer")
        assert entry.actor == "Agent"
        assert entry.action == "transfer"
        assert isinstance(entry.timestamp, datetime)
        assert entry.details == {}

    def test_custody_entry_immutable(self):
        """Test that custody entries are frozen after creation."""
        entry = CustodyEntry(actor="Agent", action="create")
        with pytest.raises((ValidationError, AttributeError)):
            entry.actor = "ModifiedAgent"


class TestArtifact:
    """Tests for the Artifact model."""

    def test_artifact_creation_minimal(self):
        """Test artifact creation with minimal required fields."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log",
        )
        assert artifact.case_id == "case-123"
        assert artifact.kind == "log"
        assert artifact.sha256 == "a" * 64
        assert artifact.s3_path == "s3://evidence/test.log"
        assert isinstance(artifact.artifact_id, uuid.UUID)
        assert isinstance(artifact.created_at, datetime)
        assert artifact.redaction_map == {}
        assert artifact.custody_chain == []

    def test_artifact_creation_full(self):
        """Test artifact creation with all fields specified."""
        artifact_id = uuid.uuid4()
        created_at = datetime.now(UTC)
        custody_entry = CustodyEntry(actor="Agent", action="create")

        artifact = Artifact(
            artifact_id=artifact_id,
            case_id="case-456",
            kind="screenshot",
            sha256="b" * 64,
            s3_path="s3://evidence/screen.png",
            redaction_map={"192.168.1.1": "REDACTED_IP"},
            custody_chain=[custody_entry],
            created_at=created_at,
            metadata={"source": "endpoint-1"},
        )

        assert artifact.artifact_id == artifact_id
        assert artifact.case_id == "case-456"
        assert artifact.redaction_map == {"192.168.1.1": "REDACTED_IP"}
        assert len(artifact.custody_chain) == 1
        assert artifact.metadata == {"source": "endpoint-1"}

    def test_artifact_sha256_validation_length(self):
        """Test SHA-256 hash length validation."""
        with pytest.raises(ValidationError) as exc_info:
            Artifact(
                case_id="case-123",
                kind="log",
                sha256="short",
                s3_path="s3://evidence/test.log",
            )
        assert "sha256" in str(exc_info.value)

    def test_artifact_sha256_validation_hex(self):
        """Test SHA-256 hash must be valid hexadecimal."""
        with pytest.raises(ValidationError) as exc_info:
            Artifact(
                case_id="case-123",
                kind="log",
                sha256="z" * 64,  # Invalid hex characters
                s3_path="s3://evidence/test.log",
            )
        assert "hexadecimal" in str(exc_info.value).lower()

    def test_artifact_sha256_normalized_to_lowercase(self):
        """Test SHA-256 hash is normalized to lowercase."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="ABCDEF" + "0" * 58,
            s3_path="s3://evidence/test.log",
        )
        assert artifact.sha256 == "abcdef" + "0" * 58

    def test_artifact_s3_path_validation(self):
        """Test S3 path must start with s3://."""
        with pytest.raises(ValidationError) as exc_info:
            Artifact(
                case_id="case-123",
                kind="log",
                sha256="a" * 64,
                s3_path="/local/path/test.log",
            )
        assert "s3://" in str(exc_info.value)

    def test_artifact_add_custody_entry(self):
        """Test adding custody entries to artifact."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log",
        )

        # Add first custody entry
        artifact_v2 = artifact.add_custody_entry(
            actor="EvidenceClerk",
            action="create",
            details={"method": "automated"},
        )

        # Original artifact unchanged
        assert len(artifact.custody_chain) == 0

        # New artifact has entry
        assert len(artifact_v2.custody_chain) == 1
        assert artifact_v2.custody_chain[0].actor == "EvidenceClerk"
        assert artifact_v2.custody_chain[0].action == "create"

        # Add second custody entry
        artifact_v3 = artifact_v2.add_custody_entry(
            actor="Analyst",
            action="review",
        )

        assert len(artifact_v2.custody_chain) == 1  # v2 unchanged
        assert len(artifact_v3.custody_chain) == 2
        assert artifact_v3.custody_chain[1].actor == "Analyst"


class TestTask:
    """Tests for the Task model."""

    def test_task_creation_minimal(self):
        """Test task creation with minimal required fields."""
        task = Task(
            case_id="case-123",
            task_type="take_snapshot",
            connector="evidence",
        )
        assert isinstance(task.task_id, str)
        assert task.case_id == "case-123"
        assert task.task_type == "take_snapshot"
        assert task.connector == "evidence"
        assert task.status == TaskStatus.PENDING
        assert task.output is None
        assert task.error_message is None
        assert isinstance(task.created_at, datetime)

    def test_task_creation_full(self):
        """Test task creation with all fields."""
        task_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)

        task = Task(
            task_id=task_id,
            case_id="case-456",
            task_type="enrich_alert",
            connector="llm",
            payload={"alert_id": "alert-123"},
            status=TaskStatus.PENDING,
            metadata={"priority": "high"},
            created_at=created_at,
        )

        assert task.task_id == task_id
        assert task.payload == {"alert_id": "alert-123"}
        assert task.metadata == {"priority": "high"}

    def test_task_timestamp_validation_started_before_created(self):
        """Test that started_at cannot be before created_at."""
        created = datetime.now(UTC)
        started = created - timedelta(seconds=10)

        with pytest.raises(ValidationError) as exc_info:
            Task(
                case_id="case-123",
                task_type="test",
                connector="test",
                created_at=created,
                started_at=started,
            )
        assert "started_at" in str(exc_info.value).lower()

    def test_task_timestamp_validation_completed_before_created(self):
        """Test that completed_at cannot be before created_at."""
        created = datetime.now(UTC)
        completed = created - timedelta(seconds=10)

        with pytest.raises(ValidationError) as exc_info:
            Task(
                case_id="case-123",
                task_type="test",
                connector="test",
                created_at=created,
                completed_at=completed,
            )
        assert "completed_at" in str(exc_info.value).lower()

    def test_task_timestamp_validation_completed_before_started(self):
        """Test that completed_at cannot be before started_at."""
        created = datetime.now(UTC)
        started = created + timedelta(seconds=5)
        completed = started - timedelta(seconds=2)

        with pytest.raises(ValidationError) as exc_info:
            Task(
                case_id="case-123",
                task_type="test",
                connector="test",
                created_at=created,
                started_at=started,
                completed_at=completed,
            )
        assert "completed_at" in str(exc_info.value).lower()

    def test_task_mark_running(self):
        """Test transitioning task to running state."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
        )

        task_running = task.mark_running()

        # Original task unchanged
        assert task.status == TaskStatus.PENDING
        assert task.started_at is None

        # New task is running
        assert task_running.status == TaskStatus.RUNNING
        assert isinstance(task_running.started_at, datetime)
        assert task_running.started_at >= task.created_at

    def test_task_mark_running_invalid_state(self):
        """Test that mark_running fails from non-pending state."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.COMPLETED,
        )

        with pytest.raises(ValueError) as exc_info:
            task.mark_running()
        assert "running" in str(exc_info.value).lower()

    def test_task_mark_completed(self):
        """Test transitioning task to completed state."""
        created = datetime.now(UTC)
        started = created + timedelta(seconds=1)
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.RUNNING,
            created_at=created,
            started_at=started,
        )

        output = {"result": "success", "data": [1, 2, 3]}
        task_completed = task.mark_completed(output)

        # Original task unchanged
        assert task.status == TaskStatus.RUNNING
        assert task.output is None

        # New task is completed
        assert task_completed.status == TaskStatus.COMPLETED
        assert task_completed.output == output
        assert isinstance(task_completed.completed_at, datetime)

    def test_task_mark_completed_invalid_state(self):
        """Test that mark_completed fails from non-running state."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.PENDING,
        )

        with pytest.raises(ValueError) as exc_info:
            task.mark_completed({"result": "success"})
        assert "completed" in str(exc_info.value).lower()

    def test_task_mark_failed(self):
        """Test transitioning task to failed state."""
        created = datetime.now(UTC)
        started = created + timedelta(seconds=1)
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.RUNNING,
            created_at=created,
            started_at=started,
        )

        error_msg = "Connection timeout"
        task_failed = task.mark_failed(error_msg)

        # Original task unchanged
        assert task.status == TaskStatus.RUNNING
        assert task.error_message is None

        # New task is failed
        assert task_failed.status == TaskStatus.FAILED
        assert task_failed.error_message == error_msg
        assert isinstance(task_failed.completed_at, datetime)

    def test_task_mark_failed_from_pending(self):
        """Test that tasks can be marked as failed from pending state."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.PENDING,
        )

        task_failed = task.mark_failed("Pre-flight check failed")
        assert task_failed.status == TaskStatus.FAILED
        assert task_failed.error_message == "Pre-flight check failed"

    def test_task_mark_failed_invalid_state(self):
        """Test that mark_failed fails from completed state."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            status=TaskStatus.COMPLETED,
        )

        with pytest.raises(ValueError) as exc_info:
            task.mark_failed("Error")
        assert "failed" in str(exc_info.value).lower()


class TestCase:
    """Tests for the Case model."""

    def test_case_creation_minimal(self):
        """Test case creation with minimal required fields."""
        case = Case(title="Test Investigation")
        assert isinstance(case.case_id, str)
        assert case.title == "Test Investigation"
        assert case.description == ""
        assert case.status == CaseStatus.OPEN
        assert case.priority == 3
        assert case.assignee is None
        assert case.tasks == []
        assert case.artifacts == []
        assert isinstance(case.created_at, datetime)
        assert isinstance(case.updated_at, datetime)

    def test_case_creation_full(self):
        """Test case creation with all fields."""
        case_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)

        case = Case(
            case_id=case_id,
            title="Critical Security Incident",
            description="Suspicious activity detected",
            status=CaseStatus.IN_PROGRESS,
            priority=1,
            assignee="security-team",
            tasks=["task-1", "task-2"],
            artifacts=["artifact-1"],
            created_at=created_at,
            metadata={"source": "automated_detection"},
        )

        assert case.case_id == case_id
        assert case.title == "Critical Security Incident"
        assert case.priority == 1
        assert case.assignee == "security-team"
        assert len(case.tasks) == 2
        assert len(case.artifacts) == 1

    def test_case_priority_validation_out_of_range(self):
        """Test that priority must be between 1 and 5."""
        with pytest.raises(ValidationError) as exc_info:
            Case(title="Test", priority=0)
        assert "priority" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            Case(title="Test", priority=6)
        assert "priority" in str(exc_info.value).lower()

    def test_case_timestamp_validation_updated_before_created(self):
        """Test that updated_at cannot be before created_at."""
        created = datetime.now(UTC)
        updated = created - timedelta(seconds=10)

        with pytest.raises(ValidationError) as exc_info:
            Case(
                title="Test",
                created_at=created,
                updated_at=updated,
            )
        assert "updated_at" in str(exc_info.value).lower()

    def test_case_timestamp_validation_closed_before_created(self):
        """Test that closed_at cannot be before created_at."""
        created = datetime.now(UTC)
        closed = created - timedelta(seconds=10)

        with pytest.raises(ValidationError) as exc_info:
            Case(
                title="Test",
                created_at=created,
                closed_at=closed,
            )
        assert "closed_at" in str(exc_info.value).lower()

    def test_case_add_task(self):
        """Test adding tasks to a case."""
        case = Case(title="Test Case")

        # Add first task
        case_v2 = case.add_task("task-1")

        # Original case unchanged
        assert len(case.tasks) == 0

        # New case has task
        assert len(case_v2.tasks) == 1
        assert "task-1" in case_v2.tasks
        assert case_v2.updated_at > case.updated_at

        # Add second task
        case_v3 = case_v2.add_task("task-2")
        assert len(case_v3.tasks) == 2
        assert "task-2" in case_v3.tasks

    def test_case_add_task_duplicate(self):
        """Test that adding duplicate task raises error."""
        case = Case(title="Test Case", tasks=["task-1"])

        with pytest.raises(ValueError) as exc_info:
            case.add_task("task-1")
        assert "already associated" in str(exc_info.value).lower()

    def test_case_add_artifact(self):
        """Test adding artifacts to a case."""
        case = Case(title="Test Case")

        # Add first artifact
        case_v2 = case.add_artifact("artifact-1")

        # Original case unchanged
        assert len(case.artifacts) == 0

        # New case has artifact
        assert len(case_v2.artifacts) == 1
        assert "artifact-1" in case_v2.artifacts
        assert case_v2.updated_at > case.updated_at

    def test_case_add_artifact_duplicate(self):
        """Test that adding duplicate artifact raises error."""
        case = Case(title="Test Case", artifacts=["artifact-1"])

        with pytest.raises(ValueError) as exc_info:
            case.add_artifact("artifact-1")
        assert "already associated" in str(exc_info.value).lower()

    def test_case_update_status(self):
        """Test updating case status."""
        case = Case(title="Test Case", status=CaseStatus.OPEN)

        # Move to in_progress
        case_v2 = case.update_status(CaseStatus.IN_PROGRESS)

        # Original case unchanged
        assert case.status == CaseStatus.OPEN

        # New case has updated status
        assert case_v2.status == CaseStatus.IN_PROGRESS
        assert case_v2.updated_at > case.updated_at
        assert case_v2.closed_at is None

    def test_case_update_status_to_closed(self):
        """Test that closing a case sets closed_at timestamp."""
        case = Case(title="Test Case", status=CaseStatus.RESOLVED)

        case_closed = case.update_status(CaseStatus.CLOSED)

        assert case_closed.status == CaseStatus.CLOSED
        assert isinstance(case_closed.closed_at, datetime)
        assert case_closed.closed_at >= case.created_at

    def test_case_update_status_closed_idempotent(self):
        """Test that closing an already-closed case doesn't change closed_at."""
        created = datetime.now(UTC) - timedelta(days=2)
        closed = datetime.now(UTC) - timedelta(days=1)
        case = Case(
            title="Test Case",
            status=CaseStatus.CLOSED,
            created_at=created,
            updated_at=closed,
            closed_at=closed,
        )
        original_closed_at = case.closed_at

        case_v2 = case.update_status(CaseStatus.CLOSED)

        # closed_at should not change
        assert case_v2.closed_at == original_closed_at


class TestModelImmutability:
    """Tests for immutability patterns across all models."""

    def test_artifact_immutability_through_methods(self):
        """Test that artifact modifications return new instances."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log",
        )

        artifact_v2 = artifact.add_custody_entry("Agent", "transfer")

        # Instances are different
        assert artifact is not artifact_v2
        assert artifact.artifact_id == artifact_v2.artifact_id
        assert len(artifact.custody_chain) == 0
        assert len(artifact_v2.custody_chain) == 1

    def test_task_immutability_through_methods(self):
        """Test that task modifications return new instances."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
        )

        task_v2 = task.mark_running()

        # Instances are different
        assert task is not task_v2
        assert task.task_id == task_v2.task_id
        assert task.status == TaskStatus.PENDING
        assert task_v2.status == TaskStatus.RUNNING

    def test_case_immutability_through_methods(self):
        """Test that case modifications return new instances."""
        case = Case(title="Test Case")

        case_v2 = case.add_task("task-1")

        # Instances are different
        assert case is not case_v2
        assert case.case_id == case_v2.case_id
        assert len(case.tasks) == 0
        assert len(case_v2.tasks) == 1


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_artifact_serialization(self):
        """Test artifact can be serialized to dict and JSON."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log",
            metadata={"source": "test"},
        )

        # To dict
        data = artifact.model_dump()
        assert data["case_id"] == "case-123"
        assert data["kind"] == "log"
        assert data["metadata"] == {"source": "test"}

        # From dict
        artifact_reloaded = Artifact.model_validate(data)
        assert artifact_reloaded.case_id == artifact.case_id
        assert artifact_reloaded.sha256 == artifact.sha256

    def test_task_serialization(self):
        """Test task can be serialized to dict and JSON."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            payload={"key": "value"},
        )

        data = task.model_dump()
        assert data["task_type"] == "test"
        assert data["payload"] == {"key": "value"}

        task_reloaded = Task.model_validate(data)
        assert task_reloaded.task_id == task.task_id

    def test_case_serialization(self):
        """Test case can be serialized to dict and JSON."""
        case = Case(
            title="Test Case",
            priority=2,
            tasks=["task-1"],
            artifacts=["artifact-1"],
        )

        data = case.model_dump()
        assert data["title"] == "Test Case"
        assert data["priority"] == 2
        assert data["tasks"] == ["task-1"]

        case_reloaded = Case.model_validate(data)
        assert case_reloaded.case_id == case.case_id
