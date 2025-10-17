# Playbooks Directory

This directory contains YAML-based playbook definitions for automated incident response scenarios.

## Available Playbooks

### 1. `email_takeover_v1.yaml`
**Scenario**: Compromised email account  
**Severity**: High  
**Tasks**: 8

Responds to a compromised email account by:
- Verifying account access
- Capturing forensic evidence
- Removing malicious email filters
- Rotating credentials
- Enabling 2FA
- Revoking OAuth tokens
- Providing security recommendations

**Required Context**:
```python
{
    "target_email": "user@example.com",
    "case_id": "INC-2024-001",
    "new_password_enc": "encrypted_password"
}
```

### 2. `device_compromise_v1.yaml`
**Scenario**: Compromised macOS endpoint  
**Severity**: Critical  
**Tasks**: 8

Responds to a compromised device by:
- Detecting malicious activity in logs
- Isolating the device on a quarantine VLAN
- Collecting forensic artifacts (memory, disk, logs)
- Terminating malicious processes
- Blocking C2 domains organization-wide
- Revoking device credentials
- Creating incident documentation
- Notifying security team

**Required Context**:
```python
{
    "device_id": "MAC-DEVICE-001",
    "osquery_log_path": "/var/log/osquery/results.log",
    "quarantine_vlan": "100",
    "case_id": "INC-2024-002",
    "notification_channel": "#incident-response"
}
```

### 3. `router_lockdown_v1.yaml`
**Scenario**: Compromised or vulnerable network router  
**Severity**: High  
**Tasks**: 9

Hardens a router by:
- Backing up current configuration
- Disabling insecure remote access (Telnet, HTTP)
- Changing admin password
- Updating firmware
- Applying access control lists
- Enabling centralized logging
- Scanning for vulnerabilities
- Verifying against hardening baseline
- Documenting all changes

**Required Context**:
```python
{
    "router_ip": "192.168.1.1",
    "case_id": "INC-2024-003",
    "new_admin_password_enc": "encrypted_password",
    "firmware_update_url": "https://updates.example.com/firmware.bin",
    "acl_rules": ["deny tcp any any eq 23", "deny tcp any any eq 80"],
    "syslog_server": "10.0.1.50",
    "hardening_checklist": "CIS_Router_v2.0"
}
```

## Usage

### Loading a Playbook

```python
from agents.commander import Commander
from pathlib import Path

# Initialize Commander with playbooks directory
commander = Commander(Path("playbooks"))

# Load a playbook with context
context = {
    "target_email": "compromised@example.com",
    "case_id": "INC-2024-042",
    "new_password_enc": "hashed_password"
}

playbook = commander.load("email_takeover_v1", context)
```

### Playbook Structure

Each playbook contains:
- **id**: Unique identifier matching the filename
- **description**: Human-readable summary
- **severity**: Incident severity level
- **tags**: Categorization tags
- **tasks**: Dictionary of task definitions with dependencies

See [full documentation](../docs/playbooks.md) for details.

## Creating New Playbooks

1. Create a new YAML file: `scenario_name_v1.yaml`
2. Define tasks with dependencies
3. Test with Commander
4. Add tests to `tests/test_commander.py`
5. Update this README

## Best Practices

- Use descriptive task names (e.g., `rotate_password`, not `pwd`)
- Mark destructive operations as `approval_required: true`
- Provide idempotency keys for tasks that shouldn't repeat
- Minimize sequential dependencies to enable parallelization
- Version playbooks with `_v1`, `_v2` suffixes

## Testing

Run tests for all playbooks:

```bash
python3 -m pytest tests/test_commander.py -v
```

Test individual playbook loading:

```bash
python3 -c "
from agents.commander import Commander
from pathlib import Path

commander = Commander(Path('playbooks'))
result = commander.load('email_takeover_v1', {'target_email': 'test@example.com', 'case_id': 'TEST', 'new_password_enc': 'pwd'})
print(f'Loaded {result[\"playbook_id\"]} with {len(result[\"tasks\"])} tasks')
"
```

## Documentation

For comprehensive documentation, see:
- [Playbook System Documentation](../docs/playbooks.md)
- [Commander Source Code](../agents/commander.py)
- [Test Suite](../tests/test_commander.py)
