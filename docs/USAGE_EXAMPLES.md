# Usage Examples

This document provides practical examples of using the utility functions in real-world scenarios.

## Example 1: Secure Logging with Redaction

Automatically redact sensitive information before logging:

```python
from utils.redactor import redact
import logging

# Setup logging with automatic redaction
class RedactingFormatter(logging.Formatter):
    def format(self, record):
        original = super().format(record)
        redacted, _ = redact(original)
        return redacted

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(RedactingFormatter('%(asctime)s - %(message)s'))
logger = logging.getLogger('secure_logger')
logger.addHandler(handler)

# Now logs are automatically redacted
logger.info("User john@example.com logged in from 555-123-4567")
# Output: "User TOK_... logged in from TOK_..."
```

## Example 2: Audit Trail with Merkle Tree

Build a tamper-evident audit trail:

```python
from utils.hasher import MerkleTree
import json
import datetime

class TamperEvidentAuditLog:
    def __init__(self):
        self.entries = []
        self.merkle_roots = []
    
    def add_entry(self, event: str, user: str, details: dict):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event": event,
            "user": user,
            "details": details,
        }
        entry_bytes = json.dumps(entry, sort_keys=True).encode()
        self.entries.append(entry_bytes)
        
        # Build Merkle tree every N entries (or periodically)
        if len(self.entries) % 10 == 0:
            tree = MerkleTree(self.entries)
            root = tree.get_root()
            self.merkle_roots.append({
                "block": len(self.entries) // 10,
                "root": root,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            print(f"Merkle root anchored: {root}")
    
    def verify_integrity(self) -> bool:
        """Verify that the audit log hasn't been tampered with."""
        if not self.entries:
            return True
        
        tree = MerkleTree(self.entries)
        current_root = tree.get_root()
        
        # Check against last anchored root
        if self.merkle_roots:
            last_anchor = self.merkle_roots[-1]
            entries_up_to_anchor = self.entries[:last_anchor["block"] * 10]
            tree_at_anchor = MerkleTree(entries_up_to_anchor)
            return tree_at_anchor.get_root() == last_anchor["root"]
        
        return True

# Usage
audit = TamperEvidentAuditLog()
audit.add_entry("login", "alice", {"ip": "192.168.1.1"})
audit.add_entry("file_access", "alice", {"path": "/secure/data.txt"})
# ... add more entries

# Verify integrity
print(f"Audit log integrity: {audit.verify_integrity()}")
```

## Example 3: Encrypted Configuration Storage

Store sensitive configuration securely:

```python
from utils.crypto import generate_key, encrypt_string, decrypt_string
import json
import os

class SecureConfig:
    def __init__(self, key_path: str = None):
        if key_path and os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                self.key = f.read()
        else:
            self.key = generate_key()
            if key_path:
                os.makedirs(os.path.dirname(key_path), exist_ok=True)
                with open(key_path, 'wb') as f:
                    f.write(self.key)
                os.chmod(key_path, 0o600)  # Read/write for owner only
    
    def save(self, config: dict, path: str):
        """Save encrypted configuration."""
        json_str = json.dumps(config, indent=2)
        encrypted = encrypt_string(json_str, key=self.key)
        with open(path, 'w') as f:
            f.write(encrypted)
    
    def load(self, path: str) -> dict:
        """Load encrypted configuration."""
        with open(path, 'r') as f:
            encrypted = f.read()
        json_str = decrypt_string(encrypted, key=self.key)
        return json.loads(json_str)

# Usage
config_mgr = SecureConfig(key_path="/secure/config.key")

# Save sensitive configuration
config = {
    "database": {
        "host": "db.example.com",
        "password": "super-secret-password",
        "api_key": "sk_live_1234567890"
    },
    "email": {
        "smtp_user": "admin@example.com",
        "smtp_password": "another-secret"
    }
}
config_mgr.save(config, "/secure/app_config.enc")

# Load configuration
loaded_config = config_mgr.load("/secure/app_config.enc")
print(loaded_config["database"]["host"])
```

## Example 4: Redacted Evidence Collection

Collect evidence while protecting PII:

```python
from utils.redactor import redact, restore
from utils.crypto import encrypt_string, decrypt_string, generate_key
from utils.hasher import sha256_string
import json

class EvidenceCollector:
    def __init__(self):
        self.encryption_key = generate_key()
        self.evidence_items = []
        self.token_maps = {}
    
    def collect(self, evidence_id: str, raw_data: str):
        """Collect evidence with automatic PII redaction."""
        # Redact PII
        redacted, token_map = redact(raw_data)
        
        # Store token map securely (encrypted)
        token_map_json = json.dumps(token_map)
        encrypted_tokens = encrypt_string(token_map_json, key=self.encryption_key)
        self.token_maps[evidence_id] = encrypted_tokens
        
        # Hash original for integrity
        original_hash = sha256_string(raw_data)
        
        # Store redacted version
        evidence = {
            "id": evidence_id,
            "redacted_data": redacted,
            "original_hash": original_hash,
        }
        self.evidence_items.append(evidence)
        
        return evidence_id
    
    def retrieve(self, evidence_id: str, authorized: bool = False) -> str:
        """Retrieve evidence, restoring PII if authorized."""
        # Find evidence
        evidence = next((e for e in self.evidence_items if e["id"] == evidence_id), None)
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found")
        
        redacted_data = evidence["redacted_data"]
        
        if authorized and evidence_id in self.token_maps:
            # Decrypt token map
            encrypted_tokens = self.token_maps[evidence_id]
            token_map_json = decrypt_string(encrypted_tokens, key=self.encryption_key)
            token_map = json.loads(token_map_json)
            
            # Restore original
            return restore(redacted_data, token_map)
        
        return redacted_data

# Usage
collector = EvidenceCollector()

# Collect evidence
evidence_data = """
Investigation log:
Suspect email: suspect@example.com
Phone: 555-987-6543
Activity detected from IP 10.0.0.5
"""

evidence_id = collector.collect("case-001-evidence-1", evidence_data)

# Retrieve redacted (for general viewing)
redacted = collector.retrieve(evidence_id, authorized=False)
print("Redacted evidence:")
print(redacted)

# Retrieve original (for authorized investigators)
original = collector.retrieve(evidence_id, authorized=True)
print("\nOriginal evidence (authorized):")
print(original)
```

## Example 5: Integration with Existing Audit System

Enhance the existing `AuditLog` class with encryption and better integrity:

```python
from core.audit import AuditLog
from utils.crypto import encrypt_string, decrypt_string, generate_key
from utils.hasher import MerkleTree
import json

class EnhancedAuditLog(AuditLog):
    def __init__(self, case_id: str, encryption_key: bytes = None):
        super().__init__(case_id)
        self.encryption_key = encryption_key or generate_key()
        self.encrypted_entries = []
    
    def record_encrypted(self, *, case_id: str, task_id: str, event: str, 
                        details: str = "", sensitive: bool = False):
        """Record an audit entry with optional encryption."""
        # Build entry
        entry = {
            "case_id": case_id,
            "task_id": task_id,
            "event": event,
            "details": details,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
        }
        
        if sensitive:
            # Encrypt sensitive entries
            entry_json = json.dumps(entry)
            encrypted = encrypt_string(entry_json, key=self.encryption_key)
            self.encrypted_entries.append({
                "encrypted": encrypted,
                "hash": sha256_string(entry_json)
            })
        else:
            # Use standard audit log
            self.record(case_id=case_id, task_id=task_id, 
                       event=event, details=details)
    
    def build_merkle_tree(self) -> str:
        """Build a Merkle tree from all audit entries."""
        # Collect all entries
        entries = []
        
        # Add standard entries
        if self.file.exists():
            with self.file.open('r') as f:
                for line in f:
                    entries.append(line.encode())
        
        # Add encrypted entries
        for enc_entry in self.encrypted_entries:
            entries.append(enc_entry["encrypted"].encode())
        
        if not entries:
            return "0" * 64
        
        tree = MerkleTree(entries)
        return tree.get_root()

# Usage
audit = EnhancedAuditLog("case-12345")

# Record normal entries
audit.record(case_id="case-12345", task_id="task-1", 
            event="investigation_started", details="Initial review")

# Record sensitive entries (encrypted)
audit.record_encrypted(case_id="case-12345", task_id="task-2",
                      event="witness_interview", 
                      details="Witness provided contact: john@example.com",
                      sensitive=True)

# Get Merkle root for anchoring
root = audit.build_merkle_tree()
print(f"Audit chain root: {root}")
# Anchor this to blockchain or timestamp authority
```

## Example 6: Tokenization for Analytics

Use deterministic tokenization to enable analytics while protecting privacy:

```python
from utils.redactor import tokenize
from collections import Counter

def analyze_access_patterns(logs: list[str]) -> dict:
    """Analyze access patterns while preserving privacy."""
    # Tokenize user identifiers
    tokenized_logs = []
    for log in logs:
        # Extract user email (simplified)
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', log)
        if email_match:
            email = email_match.group(0)
            token = tokenize(email)
            tokenized_log = log.replace(email, token)
            tokenized_logs.append((token, tokenized_log))
    
    # Now we can do analytics on tokens
    token_counts = Counter(token for token, _ in tokenized_logs)
    
    return {
        "total_accesses": len(tokenized_logs),
        "unique_users": len(token_counts),
        "top_users": token_counts.most_common(5),
    }

# Usage
logs = [
    "User alice@company.com accessed /api/data",
    "User bob@company.com accessed /api/data",
    "User alice@company.com accessed /api/users",
    "User alice@company.com accessed /api/config",
    "User charlie@company.com accessed /api/data",
]

stats = analyze_access_patterns(logs)
print(f"Unique users: {stats['unique_users']}")
print(f"Most active users (by token):")
for token, count in stats['top_users']:
    print(f"  {token}: {count} accesses")
```

## Best Practices Summary

1. **Always redact before logging**: Use redaction for any logs that might contain PII
2. **Encrypt sensitive data at rest**: Use the crypto utilities for any stored credentials or sensitive configuration
3. **Build Merkle trees for audit trails**: Periodically anchor Merkle roots to immutable storage
4. **Use deterministic tokenization wisely**: Good for analytics, but be aware of potential pattern analysis
5. **Store token maps separately**: Keep token maps encrypted and access-controlled
6. **Key management**: Use HSM or secure key storage in production, never commit keys to source control
7. **Regular integrity checks**: Periodically verify Merkle tree integrity to detect tampering
