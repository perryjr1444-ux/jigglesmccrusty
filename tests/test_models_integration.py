"""Integration tests demonstrating how core models work together in realistic scenarios.

These tests show end-to-end workflows using Case, Task, and Artifact models
to simulate typical investigation workflows in the AI SOC system.
"""

from datetime import UTC, datetime
import uuid

import pytest

from core.models import (
    Artifact,
    Case,
    CaseStatus,
    CustodyEntry,
    Task,
    TaskStatus,
)


class TestInvestigationWorkflow:
    """Test a complete investigation workflow using all models."""

    def test_complete_investigation_lifecycle(self):
        """Test a full investigation from case creation to closure."""
        
        # 1. Create a new case for suspicious activity
        case = Case(
            title="Suspicious Network Activity - Endpoint Alpha",
            description="Multiple failed login attempts followed by data exfiltration",
            priority=1,
            assignee="incident-response-team"
        )
        
        assert case.status == CaseStatus.OPEN
        assert len(case.tasks) == 0
        assert len(case.artifacts) == 0
        
        # 2. Create evidence collection task
        evidence_task = Task(
            case_id=case.case_id,
            task_type="take_snapshot",
            connector="evidence",
            payload={
                "local_path": "/var/log/auth.log",
                "kind": "log"
            }
        )
        
        # 3. Add task to case and update status
        case = case.add_task(evidence_task.task_id)
        case = case.update_status(CaseStatus.IN_PROGRESS)
        
        assert case.status == CaseStatus.IN_PROGRESS
        assert len(case.tasks) == 1
        assert evidence_task.task_id in case.tasks
        
        # 4. Execute the task
        evidence_task = evidence_task.mark_running()
        assert evidence_task.status == TaskStatus.RUNNING
        
        # 5. Task completes and creates artifact
        artifact = Artifact(
            case_id=case.case_id,
            kind="log",
            sha256="a1b2c3d4e5f67890" * 4,  # 64 hex chars
            s3_path=f"s3://evidence/{case.case_id}/auth.log"
        )
        
        # Add custody entry
        artifact = artifact.add_custody_entry(
            actor="EvidenceClerk",
            action="create",
            details={
                "source": "endpoint-alpha",
                "collection_method": "automated"
            }
        )
        
        evidence_task = evidence_task.mark_completed({
            "artifact_id": str(artifact.artifact_id),
            "s3_path": artifact.s3_path,
            "sha256": artifact.sha256
        })
        
        assert evidence_task.status == TaskStatus.COMPLETED
        assert evidence_task.output["artifact_id"] == str(artifact.artifact_id)
        
        # 6. Add artifact to case
        case = case.add_artifact(str(artifact.artifact_id))
        assert len(case.artifacts) == 1
        
        # 7. Create analysis task
        analysis_task = Task(
            case_id=case.case_id,
            task_type="enrich_alert",
            connector="llm",
            payload={
                "artifact_id": str(artifact.artifact_id),
                "analysis_type": "behavioral"
            }
        )
        
        case = case.add_task(analysis_task.task_id)
        analysis_task = analysis_task.mark_running()
        
        # 8. Analyst reviews the artifact
        artifact = artifact.add_custody_entry(
            actor="SecurityAnalyst",
            action="review",
            details={
                "reviewer": "alice@example.com",
                "findings": "confirmed_malicious"
            }
        )
        
        assert len(artifact.custody_chain) == 2
        
        # 9. Analysis completes
        analysis_task = analysis_task.mark_completed({
            "threat_level": "high",
            "indicators": ["192.168.1.100", "suspicious_user"],
            "recommendation": "isolate_endpoint"
        })
        
        # 10. Resolve and close the case
        case = case.update_status(CaseStatus.RESOLVED)
        case = case.update_status(CaseStatus.CLOSED)
        
        assert case.status == CaseStatus.CLOSED
        assert case.closed_at is not None
        assert len(case.tasks) == 2
        assert len(case.artifacts) == 1

    def test_failed_task_workflow(self):
        """Test handling of a failed task in investigation workflow."""
        
        # Create case and task
        case = Case(title="Test Investigation")
        task = Task(
            case_id=case.case_id,
            task_type="collect_memory",
            connector="forensics"
        )
        
        case = case.add_task(task.task_id)
        
        # Start task execution
        task = task.mark_running()
        
        # Task fails
        task = task.mark_failed("Insufficient permissions to access memory")
        
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Insufficient permissions to access memory"
        assert task.completed_at is not None
        
        # Case can continue with other tasks
        retry_task = Task(
            case_id=case.case_id,
            task_type="collect_memory",
            connector="forensics",
            payload={"elevated": True}
        )
        case = case.add_task(retry_task.task_id)
        
        assert len(case.tasks) == 2

    def test_multi_artifact_case(self):
        """Test case with multiple artifacts and custody transfers."""
        
        case = Case(
            title="Multi-Stage Attack Investigation",
            priority=1
        )
        
        # Collect multiple artifacts
        artifacts = []
        for i, (kind, path) in enumerate([
            ("log", "/var/log/system.log"),
            ("screenshot", "/tmp/screen.png"),
            ("memory_dump", "/tmp/memory.dmp")
        ]):
            artifact = Artifact(
                case_id=case.case_id,
                kind=kind,
                sha256=f"{i:064x}",  # Simple hash for testing
                s3_path=f"s3://evidence/{case.case_id}/{path.split('/')[-1]}"
            )
            
            # Initial custody
            artifact = artifact.add_custody_entry(
                actor="AutomatedCollector",
                action="create"
            )
            
            # Transfer to analyst
            artifact = artifact.add_custody_entry(
                actor="LeadAnalyst",
                action="transfer",
                details={"from": "evidence_vault", "to": "analysis_workspace"}
            )
            
            artifacts.append(artifact)
            case = case.add_artifact(str(artifact.artifact_id))
        
        assert len(case.artifacts) == 3
        
        # Verify all artifacts have proper custody chain
        for artifact in artifacts:
            assert len(artifact.custody_chain) == 2
            assert artifact.custody_chain[0].actor == "AutomatedCollector"
            assert artifact.custody_chain[1].actor == "LeadAnalyst"

    def test_artifact_immutability_preserves_history(self):
        """Test that artifact immutability preserves historical states."""
        
        # Create initial artifact
        artifact_v1 = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log"
        )
        
        # Add first custody entry
        artifact_v2 = artifact_v1.add_custody_entry("Agent1", "create")
        
        # Add second custody entry
        artifact_v3 = artifact_v2.add_custody_entry("Agent2", "review")
        
        # All versions exist independently
        assert len(artifact_v1.custody_chain) == 0
        assert len(artifact_v2.custody_chain) == 1
        assert len(artifact_v3.custody_chain) == 2
        
        # They all have the same artifact_id
        assert artifact_v1.artifact_id == artifact_v2.artifact_id == artifact_v3.artifact_id
        
        # But different custody chains
        assert artifact_v1.custody_chain != artifact_v2.custody_chain
        assert artifact_v2.custody_chain != artifact_v3.custody_chain

    def test_task_state_machine_enforcement(self):
        """Test that task state transitions are properly enforced."""
        
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test"
        )
        
        # Can't complete a pending task
        with pytest.raises(ValueError, match="completed"):
            task.mark_completed({"result": "success"})
        
        # Can't fail a completed task
        task_running = task.mark_running()
        task_completed = task_running.mark_completed({"result": "success"})
        
        with pytest.raises(ValueError, match="failed"):
            task_completed.mark_failed("error")
        
        # Can't run a task twice
        with pytest.raises(ValueError, match="running"):
            task_running.mark_running()

    def test_case_priority_and_timestamp_tracking(self):
        """Test case priority validation and timestamp tracking."""
        
        # Create case with valid priority
        case = Case(title="Test Case", priority=2)
        assert case.priority == 2
        
        # Priority must be 1-5
        with pytest.raises(Exception):  # ValidationError
            Case(title="Test", priority=0)
        
        with pytest.raises(Exception):  # ValidationError
            Case(title="Test", priority=6)
        
        # Timestamps are automatically managed
        initial_updated = case.updated_at
        
        # Adding a task updates the timestamp
        case_v2 = case.add_task("task-1")
        assert case_v2.updated_at > initial_updated
        
        # Closing sets closed_at
        case_closed = case_v2.update_status(CaseStatus.CLOSED)
        assert case_closed.closed_at is not None
        assert case_closed.closed_at >= case_closed.created_at


class TestModelSerialization:
    """Test that models can be serialized and deserialized correctly."""

    def test_case_roundtrip(self):
        """Test Case serialization and deserialization."""
        case = Case(
            title="Test Case",
            priority=1,
            tasks=["task-1", "task-2"],
            artifacts=["artifact-1"]
        )
        
        # Serialize
        data = case.model_dump()
        
        # Deserialize
        case_reloaded = Case.model_validate(data)
        
        assert case_reloaded.case_id == case.case_id
        assert case_reloaded.title == case.title
        assert case_reloaded.priority == case.priority
        assert case_reloaded.tasks == case.tasks

    def test_task_roundtrip(self):
        """Test Task serialization and deserialization."""
        task = Task(
            case_id="case-123",
            task_type="test",
            connector="test",
            payload={"key": "value"},
            metadata={"source": "api"}
        )
        
        data = task.model_dump()
        task_reloaded = Task.model_validate(data)
        
        assert task_reloaded.task_id == task.task_id
        assert task_reloaded.payload == task.payload

    def test_artifact_with_custody_roundtrip(self):
        """Test Artifact with custody chain serialization."""
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="s3://evidence/test.log"
        )
        
        artifact = artifact.add_custody_entry("Agent1", "create")
        artifact = artifact.add_custody_entry("Agent2", "review")
        
        data = artifact.model_dump()
        artifact_reloaded = Artifact.model_validate(data)
        
        assert len(artifact_reloaded.custody_chain) == 2
        assert artifact_reloaded.custody_chain[0].actor == "Agent1"
        assert artifact_reloaded.custody_chain[1].actor == "Agent2"
