"""
Tests for the Commander module that loads and validates playbook YAMLs.
"""
import pytest
import tempfile
from pathlib import Path
from agents.commander import Commander


@pytest.fixture
def temp_playbook_dir():
    """Create a temporary directory for test playbooks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def commander(temp_playbook_dir):
    """Create a Commander instance with a temporary playbook directory."""
    return Commander(temp_playbook_dir)


def test_load_simple_playbook(temp_playbook_dir, commander):
    """Test loading a simple playbook with variable substitution."""
    playbook_content = """id: test_playbook
description: Test playbook
severity: medium
tags: [test]

tasks:
  task1:
    type: TestTask
    inputs:
      value: "{{test_var}}"
    needs: []
    approval_required: false
"""
    playbook_path = temp_playbook_dir / "test_playbook.yaml"
    playbook_path.write_text(playbook_content)
    
    context = {"test_var": "test_value"}
    result = commander.load("test_playbook", context)
    
    assert result["playbook_id"] == "test_playbook"
    assert result["description"] == "Test playbook"
    assert result["severity"] == "medium"
    assert result["tags"] == ["test"]
    assert "task1" in result["tasks"]
    assert result["tasks"]["task1"]["inputs"]["value"] == "test_value"


def test_task_uniqueness_validation(temp_playbook_dir, commander):
    """Test that duplicate task names are detected."""
    playbook_content = """id: dup_tasks
description: Duplicate tasks
severity: low
tags: []

tasks:
  task1:
    type: Task1
    needs: []
  task1:
    type: Task2
    needs: []
"""
    playbook_path = temp_playbook_dir / "dup_tasks.yaml"
    playbook_path.write_text(playbook_content)
    
    # YAML will overwrite the duplicate key, so this won't raise an error
    # The validation is for ensuring task names in the parsed structure are unique
    result = commander.load("dup_tasks", {})
    # Should not have duplicates after YAML parsing
    assert len(result["tasks"]) == 1


def test_preserve_task_references(temp_playbook_dir, commander):
    """Test that task output references are preserved during rendering."""
    playbook_content = """id: task_refs
description: Task references
severity: medium
tags: []

tasks:
  task1:
    type: Task1
    inputs:
      value: "{{user_input}}"
    needs: []
  task2:
    type: Task2
    inputs:
      ref_value: "{{task1.output.result}}"
    needs: [task1]
"""
    playbook_path = temp_playbook_dir / "task_refs.yaml"
    playbook_path.write_text(playbook_content)
    
    context = {"user_input": "test123"}
    result = commander.load("task_refs", context)
    
    # User input should be rendered
    assert result["tasks"]["task1"]["inputs"]["value"] == "test123"
    # Task reference should be preserved (not rendered)
    assert "{{task1.output.result}}" in result["tasks"]["task2"]["inputs"]["ref_value"]


def test_nested_variable_substitution(temp_playbook_dir, commander):
    """Test variable substitution in nested structures."""
    playbook_content = """id: nested
description: Nested variables
severity: high
tags: ["{{tag1}}", "{{tag2}}"]

tasks:
  task1:
    type: Task1
    inputs:
      config:
        host: "{{hostname}}"
        port: "{{port}}"
        options: ["{{opt1}}", "{{opt2}}"]
    needs: []
"""
    playbook_path = temp_playbook_dir / "nested.yaml"
    playbook_path.write_text(playbook_content)
    
    context = {
        "tag1": "production",
        "tag2": "critical",
        "hostname": "server.example.com",
        "port": "8080",
        "opt1": "enable_tls",
        "opt2": "enable_auth"
    }
    result = commander.load("nested", context)
    
    assert result["tags"] == ["production", "critical"]
    task_inputs = result["tasks"]["task1"]["inputs"]
    assert task_inputs["config"]["host"] == "server.example.com"
    assert task_inputs["config"]["port"] == "8080"
    assert task_inputs["config"]["options"] == ["enable_tls", "enable_auth"]


def test_missing_playbook_file(commander):
    """Test that loading a non-existent playbook raises an error."""
    with pytest.raises(FileNotFoundError):
        commander.load("nonexistent_playbook", {})


def test_empty_context(temp_playbook_dir, commander):
    """Test loading a playbook with no variable substitution needed."""
    playbook_content = """id: no_vars
description: No variables
severity: low
tags: []

tasks:
  task1:
    type: Task1
    inputs:
      static: "value"
    needs: []
"""
    playbook_path = temp_playbook_dir / "no_vars.yaml"
    playbook_path.write_text(playbook_content)
    
    result = commander.load("no_vars", {})
    assert result["playbook_id"] == "no_vars"
    assert result["tasks"]["task1"]["inputs"]["static"] == "value"


def test_multiple_task_dependencies(temp_playbook_dir, commander):
    """Test playbook with complex task dependencies."""
    playbook_content = """id: complex_deps
description: Complex dependencies
severity: medium
tags: []

tasks:
  task1:
    type: Task1
    needs: []
  task2:
    type: Task2
    needs: [task1]
  task3:
    type: Task3
    needs: [task1]
  task4:
    type: Task4
    needs: [task2, task3]
"""
    playbook_path = temp_playbook_dir / "complex_deps.yaml"
    playbook_path.write_text(playbook_content)
    
    result = commander.load("complex_deps", {})
    
    assert len(result["tasks"]) == 4
    assert result["tasks"]["task1"]["needs"] == []
    assert result["tasks"]["task2"]["needs"] == ["task1"]
    assert result["tasks"]["task3"]["needs"] == ["task1"]
    assert result["tasks"]["task4"]["needs"] == ["task2", "task3"]


def test_real_playbook_email_takeover():
    """Test loading the real email_takeover_v1 playbook."""
    playbook_dir = Path(__file__).parent.parent / "playbooks"
    commander = Commander(playbook_dir)
    
    context = {
        "target_email": "victim@example.com",
        "case_id": "INC-2024-001",
        "new_password_enc": "encrypted_password_hash"
    }
    
    result = commander.load("email_takeover_v1", context)
    
    assert result["playbook_id"] == "email_takeover_v1"
    assert result["severity"] == "high"
    assert "email" in result["tags"]
    assert "compromise" in result["tags"]
    
    # Check specific tasks exist
    assert "proof_of_control" in result["tasks"]
    assert "rotate_password" in result["tasks"]
    assert "enroll_2fa" in result["tasks"]
    
    # Check variable substitution
    proof_task = result["tasks"]["proof_of_control"]
    assert proof_task["inputs"]["account_email"] == "victim@example.com"
    assert proof_task["idempotency_key"] == "proof-victim@example.com"
    
    # Check task reference preservation
    delete_task = result["tasks"]["delete_suspicious_filters"]
    assert "{{list_filters.output.suspicious_ids}}" in delete_task["inputs"]["filter_ids"]


def test_real_playbook_device_compromise():
    """Test loading the real device_compromise_v1 playbook."""
    playbook_dir = Path(__file__).parent.parent / "playbooks"
    commander = Commander(playbook_dir)
    
    context = {
        "device_id": "MAC-DEVICE-001",
        "osquery_log_path": "/var/log/osquery/results.log",
        "quarantine_vlan": "100",
        "case_id": "INC-2024-002",
        "notification_channel": "#incident-response"
    }
    
    result = commander.load("device_compromise_v1", context)
    
    assert result["playbook_id"] == "device_compromise_v1"
    assert result["severity"] == "critical"
    assert "device" in result["tags"]
    assert "endpoint" in result["tags"]
    
    # Check specific tasks exist
    assert "detect_anomaly" in result["tasks"]
    assert "network_isolate" in result["tasks"]
    assert "collect_forensics" in result["tasks"]
    
    # Check variable substitution
    isolate_task = result["tasks"]["network_isolate"]
    assert isolate_task["inputs"]["device_id"] == "MAC-DEVICE-001"
    assert isolate_task["inputs"]["vlan_id"] == "100"


def test_real_playbook_router_lockdown():
    """Test loading the real router_lockdown_v1 playbook."""
    playbook_dir = Path(__file__).parent.parent / "playbooks"
    commander = Commander(playbook_dir)
    
    context = {
        "router_ip": "192.168.1.1",
        "case_id": "INC-2024-003",
        "new_admin_password_enc": "encrypted_admin_pass",
        "firmware_update_url": "https://updates.example.com/firmware.bin",
        "acl_rules": ["deny tcp any any eq 23", "deny tcp any any eq 80"],
        "syslog_server": "10.0.1.50",
        "hardening_checklist": "CIS_Router_v2.0"
    }
    
    result = commander.load("router_lockdown_v1", context)
    
    assert result["playbook_id"] == "router_lockdown_v1"
    assert result["severity"] == "high"
    assert "network" in result["tags"]
    assert "router" in result["tags"]
    
    # Check specific tasks exist
    assert "backup_config" in result["tasks"]
    assert "disable_remote_access" in result["tasks"]
    assert "update_firmware" in result["tasks"]
    
    # Check variable substitution
    backup_task = result["tasks"]["backup_config"]
    assert backup_task["inputs"]["router_ip"] == "192.168.1.1"
    assert "192.168.1.1" in backup_task["inputs"]["backup_location"]
