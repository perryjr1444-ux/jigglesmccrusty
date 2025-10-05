# Playbook System Documentation

## Overview

The playbook system enables automated incident response through YAML-based task definitions. Each playbook defines a series of tasks that can be executed by the Orchestrator to respond to security incidents.

## Architecture

```
┌─────────────────┐
│  Playbook YAML  │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────┐
│   Commander     │ ---> │ Orchestrator │
│  (Load & Render)│      │ (Execute DAG)│
└─────────────────┘      └──────────────┘
```

### Commander Module

The `Commander` class (`agents/commander.py`) is responsible for:

1. **Loading** playbook YAML files from the playbook directory
2. **Rendering** templates with context variables using Jinja2
3. **Validating** task uniqueness and structure
4. **Returning** a structured dictionary for the Orchestrator

## Playbook Structure

### YAML Format

```yaml
id: playbook_id
description: Human-readable description of the playbook
severity: low|medium|high|critical
tags: [tag1, tag2, tag3]

tasks:
  task_name:
    type: TaskType
    inputs:
      param1: "{{variable}}"
      param2: "static_value"
    needs: [dependency_task1, dependency_task2]
    approval_required: true|false
    idempotency_key: "unique-key-{{variable}}"
```

### Fields

#### Top-Level Fields

- **id**: Unique identifier for the playbook (matches the filename without `.yaml`)
- **description**: Brief explanation of what the playbook does
- **severity**: Criticality level of the incident this playbook addresses
- **tags**: Array of categorization tags for filtering and organization

#### Task Fields

- **type**: The task executor class name (e.g., `ProofOfControl`, `NetworkIsolate`)
- **inputs**: Dictionary of parameters for the task
  - Can contain static values or Jinja2 template variables `{{variable_name}}`
  - Can reference outputs from other tasks: `{{task_name.output.field}}`
- **needs**: Array of task names that must complete before this task runs
- **approval_required**: Whether human approval is needed before execution
- **idempotency_key**: Optional key to prevent duplicate task execution

## Variable Substitution

### Context Variables

Context variables are provided when loading a playbook and are substituted during rendering:

```python
commander = Commander(Path("playbooks"))
context = {
    "target_email": "user@example.com",
    "case_id": "INC-2024-001"
}
result = commander.load("email_takeover_v1", context)
```

Variables in the YAML are replaced:
```yaml
inputs:
  account_email: "{{target_email}}"  # Becomes: "user@example.com"
  case_id: "{{case_id}}"              # Becomes: "INC-2024-001"
```

### Task References

Task output references are **preserved** during rendering for runtime resolution:

```yaml
task2:
  inputs:
    value: "{{task1.output.result}}"  # Preserved as-is for runtime
```

These references are resolved by the Orchestrator during execution when the dependent task completes.

## Available Playbooks

### 1. Email Takeover (`email_takeover_v1.yaml`)

**Purpose**: Contain a compromised email account and restore security.

**Severity**: High

**Context Variables**:
- `target_email`: The compromised email address
- `case_id`: Incident identifier
- `new_password_enc`: Encrypted new password

**Tasks**:
1. `proof_of_control` - Verify access to the account
2. `evidence_snapshot` - Capture forensic evidence
3. `list_filters` - Enumerate email filters
4. `delete_suspicious_filters` - Remove malicious filters
5. `rotate_password` - Change account password
6. `enroll_2fa` - Enable two-factor authentication
7. `revoke_oauth` - Revoke OAuth tokens
8. `hardening_coach` - Provide security recommendations

### 2. Device Compromise (`device_compromise_v1.yaml`)

**Purpose**: Isolate and forensically analyze a compromised endpoint.

**Severity**: Critical

**Context Variables**:
- `device_id`: Unique device identifier
- `osquery_log_path`: Path to OSQuery logs
- `quarantine_vlan`: VLAN ID for network isolation
- `case_id`: Incident identifier
- `notification_channel`: Alert channel (e.g., Slack)

**Tasks**:
1. `detect_anomaly` - Analyze logs for malicious activity
2. `network_isolate` - Move device to quarantine VLAN
3. `collect_forensics` - Gather memory, disk, and log artifacts
4. `terminate_processes` - Kill malicious processes
5. `block_c2_domains` - Block command-and-control domains
6. `revoke_device_credentials` - Invalidate device credentials
7. `create_incident_report` - Generate incident documentation
8. `notify_security_team` - Alert security team

### 3. Router Lockdown (`router_lockdown_v1.yaml`)

**Purpose**: Harden a compromised or vulnerable network router.

**Severity**: High

**Context Variables**:
- `router_ip`: IP address of the router
- `case_id`: Incident identifier
- `new_admin_password_enc`: Encrypted admin password
- `firmware_update_url`: URL to firmware update
- `acl_rules`: Array of ACL rules to apply
- `syslog_server`: Syslog server IP address
- `hardening_checklist`: Name of hardening baseline

**Tasks**:
1. `backup_config` - Backup current configuration
2. `disable_remote_access` - Disable Telnet, HTTP, external SSH
3. `change_admin_password` - Update admin password
4. `update_firmware` - Apply firmware update
5. `apply_acl_rules` - Configure access control lists
6. `enable_logging` - Enable syslog forwarding
7. `scan_vulnerabilities` - Run security scan
8. `verify_hardening` - Check against baseline
9. `document_changes` - Create change documentation

## Creating New Playbooks

### Step 1: Define the Scenario

Identify the security incident and the remediation steps needed.

### Step 2: Create the YAML File

Create a new file in `playbooks/` with the naming convention: `scenario_name_v1.yaml`

```yaml
id: scenario_name_v1
description: Brief description of the scenario
severity: medium
tags: [category1, category2]

tasks:
  first_task:
    type: TaskExecutorType
    inputs:
      param: "{{variable}}"
    needs: []
    approval_required: false
    idempotency_key: "unique-{{variable}}"
```

### Step 3: Define Task Dependencies

Use the `needs` field to create a task execution graph:

```yaml
task1:
  needs: []           # Runs first

task2:
  needs: [task1]      # Runs after task1

task3:
  needs: [task1]      # Runs after task1 (parallel with task2)

task4:
  needs: [task2, task3]  # Runs after both task2 and task3
```

### Step 4: Test the Playbook

```python
from agents.commander import Commander
from pathlib import Path

commander = Commander(Path("playbooks"))
context = {
    "variable": "value"
}

result = commander.load("scenario_name_v1", context)
print(f"Loaded: {result['playbook_id']}")
print(f"Tasks: {len(result['tasks'])}")
```

### Step 5: Add Tests

Add test cases to `tests/test_commander.py`:

```python
def test_new_playbook():
    playbook_dir = Path(__file__).parent.parent / "playbooks"
    commander = Commander(playbook_dir)
    
    context = {"variable": "value"}
    result = commander.load("scenario_name_v1", context)
    
    assert result["playbook_id"] == "scenario_name_v1"
    assert "task1" in result["tasks"]
```

## Usage Examples

### Loading a Playbook

```python
from agents.commander import Commander
from pathlib import Path

# Initialize Commander
commander = Commander(Path("playbooks"))

# Prepare context
context = {
    "target_email": "compromised@example.com",
    "case_id": "INC-2024-042",
    "new_password_enc": "hashed_password"
}

# Load and render the playbook
playbook = commander.load("email_takeover_v1", context)

# Access playbook metadata
print(f"ID: {playbook['playbook_id']}")
print(f"Severity: {playbook['severity']}")
print(f"Tasks: {list(playbook['tasks'].keys())}")

# Access individual tasks
for task_name, task_def in playbook['tasks'].items():
    print(f"\nTask: {task_name}")
    print(f"  Type: {task_def['type']}")
    print(f"  Needs: {task_def['needs']}")
    print(f"  Approval: {task_def['approval_required']}")
```

### Executing with Orchestrator

```python
# After loading with Commander
orchestrator = Orchestrator()
orchestrator.run_playbook(playbook)
```

## Best Practices

### 1. Task Naming

- Use descriptive, action-oriented names: `rotate_password`, not `pwd`
- Use snake_case: `enroll_2fa`, not `enrollMFA`
- Keep names unique within a playbook

### 2. Idempotency

Always provide an `idempotency_key` for tasks that should not be repeated:

```yaml
task_name:
  idempotency_key: "action-{{unique_id}}-{{timestamp}}"
```

### 3. Approval Gates

Mark destructive operations as requiring approval:

```yaml
delete_data:
  approval_required: true
```

### 4. Task Dependencies

- Minimize sequential dependencies to enable parallelization
- Group related tasks with common dependencies
- Avoid circular dependencies

### 5. Variable Naming

- Use clear, descriptive names: `target_email`, not `e`
- Use consistent naming across playbooks
- Document required variables in the playbook description

### 6. Versioning

- Include version suffix in playbook ID: `_v1`, `_v2`
- Create new versions rather than modifying existing playbooks
- Maintain backward compatibility when possible

## Validation

The Commander performs the following validations:

1. **File Existence**: Playbook YAML must exist in the playbook directory
2. **YAML Syntax**: Must be valid YAML
3. **Task Uniqueness**: Task names must be unique within a playbook
4. **Template Syntax**: Jinja2 templates must be valid

Additional validation can be performed by implementing schema validators.

## Troubleshooting

### Error: "Duplicate task names in playbook"

**Cause**: Two or more tasks have the same name.

**Solution**: Ensure all task names in the `tasks` dictionary are unique.

### Error: "File not found"

**Cause**: The playbook YAML file doesn't exist or has the wrong name.

**Solution**: Ensure the file exists at `playbooks/{playbook_id}.yaml`

### Error: Jinja2 template errors

**Cause**: Invalid Jinja2 syntax or undefined variables.

**Solution**: 
- Check template syntax: `{{variable}}` not `{variable}`
- Ensure all variables are provided in the context
- Task references should use the format: `{{task_name.output.field}}`

## Extension Points

### Custom Task Types

Implement new task executors by subclassing the base task executor:

```python
class CustomTask(BaseTaskExecutor):
    def execute(self, inputs: dict) -> dict:
        # Implementation
        return {"status": "success", "output": {...}}
```

### Custom Validators

Add custom validation logic by extending the Commander:

```python
class ExtendedCommander(Commander):
    def load(self, playbook_id: str, context: dict) -> dict:
        result = super().load(playbook_id, context)
        self._validate_custom_rules(result)
        return result
```

### Playbook Templating

Create reusable playbook templates using Jinja2 includes and extends:

```yaml
# base_template.yaml
id: "{{playbook_id}}"
description: "{{description}}"
severity: "{{severity}}"
tasks:
  # Common tasks
```

## References

- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [YAML Specification](https://yaml.org/spec/)
- [DAG Execution Model](../core/dag.py)
- [Commander Source Code](../agents/commander.py)
