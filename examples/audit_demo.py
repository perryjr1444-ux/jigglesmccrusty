#!/usr/bin/env python3
"""
Demonstration of the Tamper-Evident Audit Log (Merkle Chain)

This script demonstrates a complete red-blue-purple team exercise workflow
using the AuditLog class with Merkle chaining and anchoring.
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.audit import AuditLog

# Setup temporary directory for demo
_temp_dir = tempfile.mkdtemp()
import core.audit
core.audit._LOG_DIR = Path(_temp_dir)


def demo_red_blue_purple_exercise():
    """
    Simulate a complete security exercise with red, blue, and purple team activities.
    """
    print("=" * 80)
    print("AI SOC - Tamper-Evident Audit Log Demo")
    print("Red-Blue-Purple Team Exercise Simulation")
    print("=" * 80)
    print()
    
    # Create audit log for this exercise
    case_id = "demo_exercise_2024_001"
    audit = AuditLog(case_id=case_id)
    
    print(f"📝 Created audit log for case: {case_id}")
    print()
    
    # === RED TEAM ACTIVITIES ===
    print("🔴 RED TEAM: Generating attack scenario...")
    audit.record(
        case_id=case_id,
        task_id="red_gen_001",
        event="scenario_generated",
        details="Multi-stage macOS attack: phishing → credential theft → lateral movement"
    )
    
    print("🔴 RED TEAM: Executing attack...")
    audit.record(
        case_id=case_id,
        task_id="red_exec_001",
        event="attack_executed",
        details="Spear-phishing email delivered to target@example.com"
    )
    
    audit.record(
        case_id=case_id,
        task_id="red_exec_002",
        event="payload_deployed",
        details="Malicious payload executed: /tmp/update.bin (PID: 12345)"
    )
    
    print("   ✓ Attack scenario executed")
    print()
    
    # === BLUE TEAM ACTIVITIES ===
    print("🔵 BLUE TEAM: Monitoring and detection...")
    audit.record(
        case_id=case_id,
        task_id="blue_detect_001",
        event="alert_triggered",
        details="Suspicious process detected via OSQuery: /tmp/update.bin"
    )
    
    print("🔵 BLUE TEAM: Enriching alert...")
    audit.record(
        case_id=case_id,
        task_id="blue_enrich_001",
        event="alert_enriched",
        details="Matched red scenario, MITRE ATT&CK: T1059.004 (Unix Shell), Severity: HIGH"
    )
    
    print("🔵 BLUE TEAM: Executing response playbook...")
    audit.record(
        case_id=case_id,
        task_id="blue_playbook_001",
        event="playbook_executed",
        details="Actions: Host isolated, Forensics collected, IOCs submitted to threat intel"
    )
    
    print("   ✓ Detection and response completed")
    print()
    
    # === PURPLE TEAM ACTIVITIES ===
    print("🟣 PURPLE TEAM: Analyzing gaps...")
    audit.record(
        case_id=case_id,
        task_id="purple_gap_001",
        event="gap_analysis_complete",
        details="Detection Rate: 85%, MTTD: 42s, MTTR: 3m 15s. Gap: Lateral movement detection coverage"
    )
    
    audit.record(
        case_id=case_id,
        task_id="purple_metrics_001",
        event="metrics_computed",
        details="KPIs updated: Detection coverage improved 12% vs. last quarter"
    )
    
    print("   ✓ Gap analysis completed")
    print()
    
    # === VERIFICATION ===
    print("🔐 SECURITY: Verifying audit chain integrity...")
    is_valid = audit.verify_chain()
    if is_valid:
        print("   ✅ Chain integrity verified - No tampering detected")
    else:
        print("   ❌ ALERT: Chain integrity compromised!")
    print()
    
    # === ANCHORING ===
    print("⚓ ANCHORING: Recording chain state to external timestamp...")
    anchor_record = audit.anchor(
        anchor_data={
            "blockchain": "ethereum_testnet",
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "block_number": 12345678,
            "network": "sepolia",
            "exercise_id": "Q1_2024_macOS_Exercise",
            "participants": ["red_team", "blue_team", "purple_team"]
        }
    )
    
    print(f"   ✓ Anchored hash: {anchor_record['latest_hash'][:16]}...")
    print(f"   ✓ Timestamp: {anchor_record['timestamp']}")
    print(f"   ✓ Blockchain TX: {anchor_record['anchor_data']['tx_hash'][:16]}...")
    print()
    
    # === SUMMARY ===
    print("=" * 80)
    print("📊 AUDIT LOG SUMMARY")
    print("=" * 80)
    
    entries = audit.get_all_entries()
    print(f"Total events recorded: {len(entries)}")
    print()
    
    print("Event Timeline:")
    for i, entry_data in enumerate(entries, 1):
        entry = entry_data["entry"]
        print(f"  {i}. [{entry['task_id']}] {entry['event']}")
        print(f"     └─ {entry['details'][:60]}...")
    
    print()
    print(f"Latest chain hash: {audit.get_latest_hash()}")
    
    anchors = audit.get_anchors()
    print(f"Total anchors: {len(anchors)}")
    
    print()
    print("=" * 80)
    print("✅ Demo completed successfully!")
    print("=" * 80)


def demo_tamper_detection():
    """
    Demonstrate tamper detection capabilities.
    """
    print()
    print("=" * 80)
    print("🔍 TAMPER DETECTION DEMO")
    print("=" * 80)
    print()
    
    case_id = "demo_tamper_test"
    audit = AuditLog(case_id=case_id)
    
    # Record some events
    print("📝 Recording events...")
    audit.record(case_id=case_id, task_id="task_001", event="event_1", details="First event")
    audit.record(case_id=case_id, task_id="task_002", event="event_2", details="Second event")
    audit.record(case_id=case_id, task_id="task_003", event="event_3", details="Third event")
    
    print("✓ 3 events recorded")
    print()
    
    # Verify chain before tampering
    print("🔐 Verifying chain integrity (before tampering)...")
    is_valid = audit.verify_chain()
    print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
    print()
    
    # Demonstrate what would happen if someone tried to tamper
    print("⚠️  Note: If someone were to modify the log file directly,")
    print("    the verify_chain() method would detect the tampering.")
    print()
    
    # Show the chain hashes
    print("🔗 Chain structure:")
    entries = audit.get_entries()
    prev = "0" * 64
    for i, entry_data in enumerate(entries, 1):
        print(f"   {i}. Hash: {entry_data['hash'][:16]}... (prev: {prev[:16]}...)")
        prev = entry_data["hash"]
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        # Run the main demo
        demo_red_blue_purple_exercise()
        
        # Run tamper detection demo
        demo_tamper_detection()
        
        print()
        print("For more information, see docs/audit_log.md")
        print()
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(_temp_dir, ignore_errors=True)
