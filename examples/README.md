# Examples Directory

This directory contains example scripts and demonstrations for the playbook system.

## Demo Scripts

### `demo_commander.py`

Demonstrates how to use the Commander module to load and render playbooks with variable substitution.

**Run the demo:**
```bash
cd /home/runner/work/jigglesmccrusty/jigglesmccrusty
PYTHONPATH=. python3 examples/demo_commander.py
```

**What it shows:**
- Loading three different playbooks (email takeover, device compromise, router lockdown)
- Variable substitution with context dictionaries
- Task execution graph with dependencies
- Approval gates for sensitive operations
- Task reference preservation for runtime resolution

## Quick Start

```python
from agents.commander import Commander
from pathlib import Path

# Initialize Commander
commander = Commander(Path("playbooks"))

# Load a playbook with context
context = {
    "target_email": "user@example.com",
    "case_id": "INC-001",
    "new_password_enc": "encrypted_pwd"
}

playbook = commander.load("email_takeover_v1", context)

# Access playbook data
print(f"Loaded: {playbook['playbook_id']}")
print(f"Tasks: {len(playbook['tasks'])}")
```

## More Information

- [Playbook Documentation](../docs/playbooks.md)
- [Playbook Directory](../playbooks/)
- [Test Suite](../tests/test_commander.py)
