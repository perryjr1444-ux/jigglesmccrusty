"""Example usage of core data contract models.

This script demonstrates how to use Case, Task, and Artifact models
in typical AI SOC workflows.
"""

from core.models import (
    Artifact,
    Case,
    CaseStatus,
    CustodyEntry,
    Task,
    TaskStatus,
)


def example_basic_case_creation():
    """Example: Creating a new case."""
    print("=" * 60)
    print("Example 1: Basic Case Creation")
    print("=" * 60)
    
    case = Case(
        title="Suspicious Login Activity",
        description="Multiple failed SSH login attempts detected",
        priority=2,
        assignee="security-team"
    )
    
    print(f"Created case: {case.case_id}")
    print(f"  Title: {case.title}")
    print(f"  Status: {case.status}")
    print(f"  Priority: {case.priority}")
    print(f"  Created: {case.created_at}")
    print()


def example_task_lifecycle():
    """Example: Task state transitions."""
    print("=" * 60)
    print("Example 2: Task Lifecycle")
    print("=" * 60)
    
    # Create a task
    task = Task(
        case_id="case-123",
        task_type="collect_logs",
        connector="evidence",
        payload={
            "path": "/var/log/auth.log",
            "lines": 1000
        }
    )
    
    print(f"Created task: {task.task_id}")
    print(f"  Status: {task.status} (PENDING)")
    
    # Start execution
    task = task.mark_running()
    print(f"  Status: {task.status} (RUNNING)")
    
    # Complete successfully
    task = task.mark_completed({
        "lines_collected": 1000,
        "artifact_id": "artifact-456"
    })
    print(f"  Status: {task.status} (COMPLETED)")
    print(f"  Output: {task.output}")
    print()


def example_artifact_with_custody():
    """Example: Artifact with chain of custody."""
    print("=" * 60)
    print("Example 3: Artifact Chain of Custody")
    print("=" * 60)
    
    # Create artifact
    artifact = Artifact(
        case_id="case-789",
        kind="log",
        sha256="1234567890abcdef" * 4,
        s3_path="s3://evidence/case-789/auth.log"
    )
    
    print(f"Created artifact: {artifact.artifact_id}")
    print(f"  Kind: {artifact.kind}")
    print(f"  SHA-256: {artifact.sha256[:16]}...")
    print(f"  S3 Path: {artifact.s3_path}")
    
    # Add custody entries
    artifact = artifact.add_custody_entry(
        actor="EvidenceCollector",
        action="create",
        details={"method": "automated"}
    )
    
    artifact = artifact.add_custody_entry(
        actor="ForensicAnalyst",
        action="review",
        details={"analyst": "alice@example.com"}
    )
    
    print(f"\nCustody Chain ({len(artifact.custody_chain)} entries):")
    for i, entry in enumerate(artifact.custody_chain, 1):
        print(f"  {i}. {entry.actor} - {entry.action} at {entry.timestamp}")
    print()


def example_complete_workflow():
    """Example: Complete investigation workflow."""
    print("=" * 60)
    print("Example 4: Complete Investigation Workflow")
    print("=" * 60)
    
    # 1. Create case
    case = Case(
        title="Data Exfiltration Investigation",
        description="Unusual outbound traffic detected",
        priority=1
    )
    print(f"1. Created case: {case.case_id}")
    
    # 2. Create and add evidence collection task
    task = Task(
        case_id=case.case_id,
        task_type="capture_network",
        connector="pcap"
    )
    case = case.add_task(task.task_id)
    print(f"2. Added task: {task.task_id}")
    
    # 3. Update case status
    case = case.update_status(CaseStatus.IN_PROGRESS)
    print(f"3. Updated case status: {case.status}")
    
    # 4. Execute task
    task = task.mark_running()
    task = task.mark_completed({
        "packets_captured": 5000,
        "artifact_id": "artifact-123"
    })
    print(f"4. Task completed: {task.status}")
    
    # 5. Create artifact
    artifact = Artifact(
        case_id=case.case_id,
        kind="pcap",
        sha256="abcdef1234567890" * 4,
        s3_path=f"s3://evidence/{case.case_id}/capture.pcap"
    )
    artifact = artifact.add_custody_entry("NetworkMonitor", "create")
    case = case.add_artifact(str(artifact.artifact_id))
    print(f"5. Added artifact: {artifact.artifact_id}")
    
    # 6. Close case
    case = case.update_status(CaseStatus.RESOLVED)
    case = case.update_status(CaseStatus.CLOSED)
    print(f"6. Closed case at: {case.closed_at}")
    
    print(f"\nFinal Summary:")
    print(f"  Tasks: {len(case.tasks)}")
    print(f"  Artifacts: {len(case.artifacts)}")
    print(f"  Status: {case.status}")
    print()


def example_immutability_pattern():
    """Example: Immutability through copy-on-write."""
    print("=" * 60)
    print("Example 5: Immutability Pattern")
    print("=" * 60)
    
    # Create initial case
    case_v1 = Case(title="Version 1")
    print(f"V1: {case_v1.case_id} - {len(case_v1.tasks)} tasks")
    
    # Add task creates new version
    case_v2 = case_v1.add_task("task-1")
    print(f"V2: {case_v2.case_id} - {len(case_v2.tasks)} tasks")
    
    # Add another task
    case_v3 = case_v2.add_task("task-2")
    print(f"V3: {case_v3.case_id} - {len(case_v3.tasks)} tasks")
    
    # Original versions unchanged
    print(f"\nOriginal V1 still has: {len(case_v1.tasks)} tasks")
    print(f"Original V2 still has: {len(case_v2.tasks)} tasks")
    print(f"Current V3 has: {len(case_v3.tasks)} tasks")
    print()


def example_validation():
    """Example: Model validation."""
    print("=" * 60)
    print("Example 6: Validation Examples")
    print("=" * 60)
    
    # Valid artifact
    try:
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,  # Valid 64-char hex
            s3_path="s3://evidence/test.log"  # Valid S3 path
        )
        print("✓ Valid artifact created successfully")
    except Exception as e:
        print(f"✗ Validation error: {e}")
    
    # Invalid SHA-256 (too short)
    try:
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="short",
            s3_path="s3://evidence/test.log"
        )
        print("✗ Should have failed validation")
    except Exception as e:
        print(f"✓ Caught validation error: SHA-256 too short")
    
    # Invalid S3 path
    try:
        artifact = Artifact(
            case_id="case-123",
            kind="log",
            sha256="a" * 64,
            s3_path="/local/path/test.log"
        )
        print("✗ Should have failed validation")
    except Exception as e:
        print(f"✓ Caught validation error: Invalid S3 path")
    
    # Invalid case priority
    try:
        case = Case(
            title="Test",
            priority=10  # Out of range (1-5)
        )
        print("✗ Should have failed validation")
    except Exception as e:
        print(f"✓ Caught validation error: Invalid priority")
    
    print()


def example_serialization():
    """Example: Serialization and deserialization."""
    print("=" * 60)
    print("Example 7: Serialization")
    print("=" * 60)
    
    # Create a case
    case = Case(
        title="Test Case",
        priority=2,
        tasks=["task-1", "task-2"]
    )
    
    # Serialize to dict
    data = case.model_dump()
    print(f"Serialized to dict: {list(data.keys())}")
    
    # Deserialize from dict
    case_reloaded = Case.model_validate(data)
    print(f"Deserialized: {case_reloaded.case_id}")
    print(f"  Same ID: {case.case_id == case_reloaded.case_id}")
    print(f"  Same tasks: {case.tasks == case_reloaded.tasks}")
    print()


if __name__ == "__main__":
    example_basic_case_creation()
    example_task_lifecycle()
    example_artifact_with_custody()
    example_complete_workflow()
    example_immutability_pattern()
    example_validation()
    example_serialization()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
