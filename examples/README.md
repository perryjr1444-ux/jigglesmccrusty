# Orchestrator Examples

This directory contains example scripts demonstrating how to use the orchestrator and DAG task execution framework.

## Running the Demo

```bash
python3 examples/orchestrator_demo.py
```

## What the Demo Shows

The demo script (`orchestrator_demo.py`) demonstrates the following features:

### 1. Basic Playbook Execution
- Creating a playbook with task dependencies
- Auto-approving tasks that require approval
- Sequential execution based on dependencies

### 2. Manual Approval Workflow
- Tasks that wait for manual approval
- Retrieving tasks by status
- Approving tasks programmatically

### 3. Idempotency
- Preventing duplicate execution using idempotency keys
- Sharing idempotency state across orchestrator instances
- Skipping already-executed tasks

### 4. Policy Enforcement
- Implementing custom policy checkers
- Blocking tasks based on policy rules
- Recording policy decisions in audit logs

### 5. DAG Layer Execution
- Visualizing task dependencies
- Understanding execution layers
- Identifying tasks that can run in parallel

## Expected Output

When you run the demo, you should see output similar to:

```
████████████████████████████████████████████████████████████
  ORCHESTRATOR & DAG TASK EXECUTION FRAMEWORK DEMO
████████████████████████████████████████████████████████████

============================================================
DEMO 1: Basic Playbook Execution (Auto-Approve)
============================================================

🚀 Starting playbook execution...
  📧 Listing email filters for victim@example.com
  🗑️  Deleting 2 suspicious filters

📊 Execution Results:
  ✅ proof: TaskStatus.COMPLETED
  ✅ list_filters: TaskStatus.COMPLETED
  ✅ delete_filters: TaskStatus.COMPLETED

[... more demos ...]

✅ All demos completed successfully!
```

## Creating Your Own Playbook

To use the orchestrator with your own playbook:

1. **Define the playbook structure**:
```python
playbook = {
    "playbook_id": "my_playbook",
    "tasks": {
        "task1": {
            "type": "TaskType1",
            "inputs": {...},
            "needs": [],  # Dependencies
            "approval_required": False,
            "idempotency_key": "optional-key",
        }
    }
}
```

2. **Setup connectors**:
```python
from core.connectors import ConnectorRegistry

registry = ConnectorRegistry(token_provider=get_token)
```

3. **Create orchestrator**:
```python
from core.orchestrator import Orchestrator

orchestrator = Orchestrator(
    connector_registry=registry,
    policy_checker=my_policy_function,  # Optional
    idempotency_store=my_store  # Optional
)
```

4. **Execute playbook**:
```python
result = await orchestrator.run_playbook(
    playbook=playbook,
    case_id="unique_case_id",
    context={"var": "value"},
    auto_approve=False
)
```

## See Also

- [Orchestration Documentation](../docs/ORCHESTRATION.md) - Complete guide
- [DAG Tests](../tests/test_dag.py) - Unit tests for DAG
- [Orchestrator Tests](../tests/test_orchestrator.py) - Unit tests for orchestrator
- [Email Takeover Playbook](../playbooks/email_takeover_v1.yaml) - Real playbook example
