#!/usr/bin/env python3
"""
Demo script showing how to use the Commander to load and render playbooks.
"""
from agents.commander import Commander
from pathlib import Path
import json


def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_playbook(commander, playbook_id, context, description):
    print_section(f"DEMO: {description}")
    
    print(f"\n📋 Loading playbook: {playbook_id}")
    print(f"📝 Context variables:")
    for key, value in context.items():
        if isinstance(value, list):
            print(f"   {key}: [{', '.join(str(v) for v in value[:2])}...]" if len(value) > 2 else f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    # Load the playbook
    result = commander.load(playbook_id, context)
    
    print(f"\n✅ Successfully loaded playbook")
    print(f"   ID: {result['playbook_id']}")
    print(f"   Description: {result['description']}")
    print(f"   Severity: {result['severity']}")
    print(f"   Tags: {', '.join(result['tags'])}")
    print(f"   Tasks: {len(result['tasks'])}")
    
    print(f"\n📊 Task Execution Graph:")
    for task_name, task_def in result['tasks'].items():
        deps = ', '.join(task_def['needs']) if task_def['needs'] else 'none'
        approval = '🔒' if task_def.get('approval_required', False) else '✓'
        print(f"   {approval} {task_name}")
        print(f"      Type: {task_def['type']}")
        print(f"      Dependencies: {deps}")
        
        # Show a sample input to demonstrate variable rendering
        if task_def['inputs']:
            sample_key = list(task_def['inputs'].keys())[0]
            sample_value = task_def['inputs'][sample_key]
            if isinstance(sample_value, str) and len(sample_value) < 50:
                print(f"      Sample input: {sample_key} = {sample_value}")


def main():
    print_section("COMMANDER PLAYBOOK DEMO")
    print("\nThis demo shows how the Commander module loads and renders")
    print("playbook YAMLs with variable substitution and task validation.")
    
    # Initialize Commander
    playbook_dir = Path(__file__).parent.parent / "playbooks"
    commander = Commander(playbook_dir)
    print(f"\n✓ Commander initialized with playbook directory: {playbook_dir}")
    
    # Demo 1: Email Takeover
    demo_playbook(
        commander,
        "email_takeover_v1",
        {
            "target_email": "victim@corporation.com",
            "case_id": "INC-2024-042",
            "new_password_enc": "SHA256:a3f2b1c9..."
        },
        "Email Account Takeover Response"
    )
    
    # Demo 2: Device Compromise
    demo_playbook(
        commander,
        "device_compromise_v1",
        {
            "device_id": "MAC-LAPTOP-0157",
            "osquery_log_path": "/var/log/osquery/results.log",
            "quarantine_vlan": "999",
            "case_id": "INC-2024-043",
            "notification_channel": "#security-incidents"
        },
        "Compromised Device Containment"
    )
    
    # Demo 3: Router Lockdown
    demo_playbook(
        commander,
        "router_lockdown_v1",
        {
            "router_ip": "10.0.100.1",
            "case_id": "INC-2024-044",
            "new_admin_password_enc": "bcrypt:$2b$12$...",
            "firmware_update_url": "https://vendor.com/fw/v2.1.3.bin",
            "acl_rules": [
                "deny tcp any any eq 23",
                "deny tcp any any eq 80",
                "permit tcp any any eq 443"
            ],
            "syslog_server": "10.0.50.100",
            "hardening_checklist": "CIS_Router_Benchmark_v2.0"
        },
        "Network Router Hardening"
    )
    
    print_section("DEMO COMPLETE")
    print("\n✅ All playbooks loaded and validated successfully!")
    print("\nNext steps:")
    print("  1. Pass the loaded playbook to the Orchestrator")
    print("  2. Orchestrator builds a DAG from task dependencies")
    print("  3. Tasks execute in parallel where possible")
    print("  4. Approval gates pause execution for human review")
    print("  5. Task outputs are passed to dependent tasks")
    print("\nFor more information, see:")
    print("  - docs/playbooks.md")
    print("  - playbooks/README.md")
    print("  - tests/test_commander.py")


if __name__ == "__main__":
    main()
