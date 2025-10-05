import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.audit import AuditLog, _LOG_DIR


class TestAuditLog:
    """Test suite for the tamper-evident AuditLog with Merkle chaining."""
    
    def setup_method(self):
        """Set up a temporary log directory for each test."""
        # Create a temp directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = _LOG_DIR
        # Monkey-patch the log directory for testing
        import core.audit
        core.audit._LOG_DIR = Path(self.temp_dir)
        
    def teardown_method(self):
        """Clean up the temporary log directory after each test."""
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        # Restore original log directory
        import core.audit
        core.audit._LOG_DIR = self.original_log_dir
    
    def test_create_audit_log(self):
        """Test creating a new audit log instance."""
        audit = AuditLog(case_id="test_case_001")
        assert audit.case_id == "test_case_001"
        assert audit.file.name == "test_case_001.log"
    
    def test_record_single_entry(self):
        """Test recording a single audit entry."""
        audit = AuditLog(case_id="test_case_002")
        
        audit.record(
            case_id="test_case_002",
            task_id="task_001",
            event="user_login",
            details="User admin logged in"
        )
        
        # Verify file was created
        assert audit.file.exists()
        
        # Verify entry can be read
        entries = audit.get_entries()
        assert len(entries) == 1
        assert entries[0]["entry"]["case_id"] == "test_case_002"
        assert entries[0]["entry"]["task_id"] == "task_001"
        assert entries[0]["entry"]["event"] == "user_login"
        assert entries[0]["entry"]["details"] == "User admin logged in"
    
    def test_merkle_chain_hashing(self):
        """Test that entries are properly chained with Merkle hashing."""
        audit = AuditLog(case_id="test_case_003")
        
        # Record multiple entries
        audit.record(
            case_id="test_case_003",
            task_id="task_001",
            event="event_1",
            details="First event"
        )
        
        audit.record(
            case_id="test_case_003",
            task_id="task_002",
            event="event_2",
            details="Second event"
        )
        
        audit.record(
            case_id="test_case_003",
            task_id="task_003",
            event="event_3",
            details="Third event"
        )
        
        # Verify chain integrity
        assert audit.verify_chain()
        
        entries = audit.get_entries()
        assert len(entries) == 3
        
        # Verify each hash is different
        hashes = [entry["hash"] for entry in entries]
        assert len(set(hashes)) == 3  # All hashes should be unique
    
    def test_get_latest_hash(self):
        """Test retrieving the latest hash from the chain."""
        audit = AuditLog(case_id="test_case_004")
        
        # Empty log should return genesis hash (64 zeros)
        latest = audit.get_latest_hash()
        assert latest == "0" * 64
        
        # Record an entry
        audit.record(
            case_id="test_case_004",
            task_id="task_001",
            event="test_event",
            details="Test"
        )
        
        # Latest hash should now be different
        latest = audit.get_latest_hash()
        assert latest != "0" * 64
        assert len(latest) == 64  # SHA-256 produces 64 hex characters
        
        # Verify it matches the last entry's hash
        entries = audit.get_entries()
        assert latest == entries[-1]["hash"]
    
    def test_get_entries_with_limit(self):
        """Test retrieving a limited number of entries."""
        audit = AuditLog(case_id="test_case_005")
        
        # Record 10 entries
        for i in range(10):
            audit.record(
                case_id="test_case_005",
                task_id=f"task_{i:03d}",
                event=f"event_{i}",
                details=f"Event number {i}"
            )
        
        # Get all entries
        all_entries = audit.get_entries()
        assert len(all_entries) == 10
        
        # Get last 3 entries
        limited = audit.get_entries(limit=3)
        assert len(limited) == 3
        assert limited[-1]["entry"]["task_id"] == "task_009"
        assert limited[0]["entry"]["task_id"] == "task_007"
    
    def test_get_all_entries(self):
        """Test get_all_entries is an alias for get_entries without limit."""
        audit = AuditLog(case_id="test_case_006")
        
        # Record some entries
        for i in range(5):
            audit.record(
                case_id="test_case_006",
                task_id=f"task_{i}",
                event=f"event_{i}",
                details=""
            )
        
        all_entries = audit.get_all_entries()
        assert len(all_entries) == 5
    
    def test_verify_chain_with_tampering(self):
        """Test that chain verification detects tampering."""
        audit = AuditLog(case_id="test_case_007")
        
        # Record entries
        audit.record(
            case_id="test_case_007",
            task_id="task_001",
            event="event_1",
            details="First"
        )
        
        audit.record(
            case_id="test_case_007",
            task_id="task_002",
            event="event_2",
            details="Second"
        )
        
        # Verify chain is valid
        assert audit.verify_chain()
        
        # Tamper with the log file (modify an entry)
        with audit.file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if len(lines) > 0:
            # Change the first line's content (but keep the hash)
            parts = lines[0].rsplit(" ", 1)
            if len(parts) == 2:
                entry_json, entry_hash = parts
                entry = json.loads(entry_json)
                entry["details"] = "TAMPERED"
                tampered_json = json.dumps(entry, separators=(",", ":"))
                lines[0] = f"{tampered_json} {entry_hash}\n"
                
                with audit.file.open("w", encoding="utf-8") as f:
                    f.writelines(lines)
                
                # Verification should now fail
                assert not audit.verify_chain()
    
    def test_anchor_chain(self):
        """Test anchoring the chain state."""
        audit = AuditLog(case_id="test_case_008")
        
        # Record some entries
        audit.record(
            case_id="test_case_008",
            task_id="task_001",
            event="event_1",
            details="First"
        )
        
        audit.record(
            case_id="test_case_008",
            task_id="task_002",
            event="event_2",
            details="Second"
        )
        
        # Anchor the chain
        latest_hash_before = audit.get_latest_hash()
        anchor_record = audit.anchor(
            anchor_data={
                "blockchain": "ethereum",
                "tx_id": "0x1234567890abcdef",
                "block_number": 12345678
            }
        )
        
        # Verify anchor record
        assert anchor_record["case_id"] == "test_case_008"
        assert anchor_record["latest_hash"] == latest_hash_before
        assert "timestamp" in anchor_record
        assert anchor_record["anchor_data"]["blockchain"] == "ethereum"
        assert anchor_record["anchor_data"]["tx_id"] == "0x1234567890abcdef"
    
    def test_get_anchors(self):
        """Test retrieving anchor records."""
        audit = AuditLog(case_id="test_case_009")
        
        # Initially, no anchors
        anchors = audit.get_anchors()
        assert len(anchors) == 0
        
        # Record and anchor
        audit.record(
            case_id="test_case_009",
            task_id="task_001",
            event="event_1",
            details="First"
        )
        
        audit.anchor(anchor_data={"source": "timestamp_authority_1"})
        
        # Add more entries and anchor again
        audit.record(
            case_id="test_case_009",
            task_id="task_002",
            event="event_2",
            details="Second"
        )
        
        audit.anchor(anchor_data={"source": "timestamp_authority_2"})
        
        # Retrieve anchors
        anchors = audit.get_anchors()
        assert len(anchors) == 2
        assert anchors[0]["anchor_data"]["source"] == "timestamp_authority_1"
        assert anchors[1]["anchor_data"]["source"] == "timestamp_authority_2"
        
        # Verify hashes are different (chain progressed)
        assert anchors[0]["latest_hash"] != anchors[1]["latest_hash"]
    
    def test_empty_log_operations(self):
        """Test operations on an empty log."""
        audit = AuditLog(case_id="test_case_010")
        
        # Get entries from empty log
        entries = audit.get_entries()
        assert len(entries) == 0
        
        # Verify empty chain
        assert audit.verify_chain()
        
        # Get latest hash (should be genesis)
        latest = audit.get_latest_hash()
        assert latest == "0" * 64
        
        # Get anchors from empty log
        anchors = audit.get_anchors()
        assert len(anchors) == 0
    
    def test_mock_scenario_red_blue_purple(self):
        """
        Test with a mock red-blue-purple team scenario to demonstrate
        audit log usage in the AI SOC context.
        """
        audit = AuditLog(case_id="incident_2024_001")
        
        # Red team generates attack scenario
        audit.record(
            case_id="incident_2024_001",
            task_id="red_gen_001",
            event="red_scenario_generated",
            details="Multi-stage attack targeting macOS endpoint"
        )
        
        # Red team executes attack
        audit.record(
            case_id="incident_2024_001",
            task_id="red_exec_001",
            event="attack_executed",
            details="Phishing email sent, payload delivered"
        )
        
        # Blue team detects activity
        audit.record(
            case_id="incident_2024_001",
            task_id="blue_detect_001",
            event="detection_triggered",
            details="Suspicious process execution detected via OSQuery"
        )
        
        # Blue team enriches alert
        audit.record(
            case_id="incident_2024_001",
            task_id="blue_enrich_001",
            event="alert_enriched",
            details="Alert matched with red scenario, MITRE ATT&CK: T1059"
        )
        
        # Blue team executes playbook
        audit.record(
            case_id="incident_2024_001",
            task_id="blue_playbook_001",
            event="playbook_executed",
            details="Containment actions: isolate host, collect forensics"
        )
        
        # Purple team analyzes gaps
        audit.record(
            case_id="incident_2024_001",
            task_id="purple_gap_001",
            event="gap_analysis_complete",
            details="Detection delay: 45s, Coverage: 85%, Gaps identified in lateral movement detection"
        )
        
        # Anchor the complete incident log
        anchor = audit.anchor(
            anchor_data={
                "blockchain": "ethereum_testnet",
                "tx_hash": "0xabcdef1234567890",
                "timestamp_authority": "RFC3161_TSA",
                "signature": "mock_signature_data"
            }
        )
        
        # Verify the audit trail
        entries = audit.get_all_entries()
        assert len(entries) == 6
        assert audit.verify_chain()
        
        # Verify all team activities are logged
        events = [e["entry"]["event"] for e in entries]
        assert "red_scenario_generated" in events
        assert "detection_triggered" in events
        assert "gap_analysis_complete" in events
        
        # Verify anchor was created
        assert anchor["case_id"] == "incident_2024_001"
        assert "tx_hash" in anchor["anchor_data"]


def test_audit_log_basic():
    """Standalone test that can be run with pytest."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Monkey-patch log directory
        import core.audit
        original_dir = core.audit._LOG_DIR
        core.audit._LOG_DIR = Path(temp_dir)
        
        audit = AuditLog(case_id="standalone_test")
        audit.record(
            case_id="standalone_test",
            task_id="task_001",
            event="test_event",
            details="Testing audit log"
        )
        
        entries = audit.get_entries()
        assert len(entries) == 1
        assert entries[0]["entry"]["event"] == "test_event"
        
        # Restore
        core.audit._LOG_DIR = original_dir
    finally:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Allow running tests directly with python
    import pytest
    pytest.main([__file__, "-v"])
