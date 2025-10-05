# Tamper-Evident Audit Log (Merkle Chain)

## Overview

The `AuditLog` class provides a tamper-evident, append-only logging mechanism for the AI-Powered Security Operations Center (AI SOC). Each log entry is cryptographically hashed together with the previous entry to create a Merkle chain, ensuring data integrity and detecting any unauthorized modifications.

## Key Features

- **Append-Only Design**: Once written, entries cannot be modified or deleted
- **Merkle Chaining**: Each entry is hashed with the previous hash, creating a cryptographic chain
- **Tamper Detection**: Built-in verification method to detect any modifications to the log
- **Anchoring Support**: Ability to anchor chain state to external timestamps or blockchains
- **Audit Trail**: Complete history of all security operations across red, blue, and purple teams

## Architecture

### Chain Structure

```
Entry 1 → Hash 1 (based on Genesis + Entry 1)
Entry 2 → Hash 2 (based on Hash 1 + Entry 2)
Entry 3 → Hash 3 (based on Hash 2 + Entry 3)
...
Entry N → Hash N (based on Hash N-1 + Entry N)
```

The genesis hash (initial state) is `0000...0000` (64 zeros).

### Log Format

Each line in the log file contains:
```
<JSON_ENTRY> <SHA256_HASH>
```

Example:
```json
{"case_id":"incident_001","task_id":"task_001","event":"user_login","details":"Admin login","ts":"2024-01-15T10:30:00Z"} a1b2c3d4e5f6...
```

### Anchor Records

Anchor records are stored separately in `<case_id>_anchors.json` and contain:
- `case_id`: The case identifier
- `latest_hash`: The hash being anchored
- `timestamp`: ISO 8601 timestamp of anchoring
- `anchor_data`: External anchoring metadata (blockchain TX, timestamp authority signature, etc.)

## Usage

### Basic Operations

#### 1. Create an Audit Log

```python
from core.audit import AuditLog

# Create a log for a specific case
audit = AuditLog(case_id="incident_2024_001")
```

#### 2. Record Events

```python
# Record a security event
audit.record(
    case_id="incident_2024_001",
    task_id="blue_detect_001",
    event="detection_triggered",
    details="Suspicious process execution detected via OSQuery"
)
```

#### 3. Retrieve Entries

```python
# Get all entries
all_entries = audit.get_all_entries()

# Get last N entries
recent = audit.get_entries(limit=10)

# Each entry contains:
# {
#   "entry": {
#     "case_id": "...",
#     "task_id": "...",
#     "event": "...",
#     "details": "...",
#     "ts": "..."
#   },
#   "hash": "..."
# }
```

#### 4. Get Latest Hash

```python
# Retrieve the current chain head hash
latest_hash = audit.get_latest_hash()
```

#### 5. Verify Chain Integrity

```python
# Verify the entire chain is valid
is_valid = audit.verify_chain()

if not is_valid:
    # Chain has been tampered with!
    print("WARNING: Audit log has been modified!")
```

### Anchoring

Anchoring provides an immutable, external proof of the log state at a specific time.

#### Anchor to Blockchain

```python
# Anchor to Ethereum blockchain
anchor_record = audit.anchor(
    anchor_data={
        "blockchain": "ethereum",
        "network": "mainnet",
        "tx_hash": "0x1234567890abcdef...",
        "block_number": 18500000,
        "gas_used": "21000"
    }
)

# Returns:
# {
#   "case_id": "incident_2024_001",
#   "latest_hash": "a1b2c3...",
#   "timestamp": "2024-01-15T10:45:00Z",
#   "anchor_data": { ... }
# }
```

#### Anchor to Timestamp Authority

```python
# Anchor to RFC 3161 Timestamp Authority
anchor_record = audit.anchor(
    anchor_data={
        "authority": "RFC3161_TSA",
        "url": "https://timestamp.example.com",
        "signature": "base64_encoded_signature...",
        "certificate": "base64_encoded_cert..."
    }
)
```

#### Retrieve Anchor History

```python
# Get all anchors for this case
anchors = audit.get_anchors()

for anchor in anchors:
    print(f"Anchored at {anchor['timestamp']}")
    print(f"Hash: {anchor['latest_hash']}")
```

## Red-Blue-Purple Team Integration

### Red Team Usage

```python
audit = AuditLog(case_id="exercise_2024_q1")

# Log attack scenario generation
audit.record(
    case_id="exercise_2024_q1",
    task_id="red_gen_001",
    event="scenario_generated",
    details="Multi-stage macOS attack: phishing → payload → persistence"
)

# Log attack execution
audit.record(
    case_id="exercise_2024_q1",
    task_id="red_exec_001",
    event="attack_executed",
    details="Payload delivered via spear-phishing email"
)
```

### Blue Team Usage

```python
# Log detection
audit.record(
    case_id="exercise_2024_q1",
    task_id="blue_detect_001",
    event="alert_triggered",
    details="Suspicious process: /tmp/malware.bin, PID: 12345"
)

# Log enrichment
audit.record(
    case_id="exercise_2024_q1",
    task_id="blue_enrich_001",
    event="alert_enriched",
    details="Matched red scenario, MITRE ATT&CK: T1059.004"
)

# Log response
audit.record(
    case_id="exercise_2024_q1",
    task_id="blue_playbook_001",
    event="playbook_executed",
    details="Actions: host isolation, forensic collection, IOC submission"
)
```

### Purple Team Usage

```python
# Log gap analysis
audit.record(
    case_id="exercise_2024_q1",
    task_id="purple_gap_001",
    event="gap_analysis_complete",
    details="Detection rate: 80%, MTTD: 45s, Gaps: lateral movement visibility"
)

# Anchor the complete exercise
anchor = audit.anchor(
    anchor_data={
        "exercise": "Q1_2024_macOS_endpoint",
        "blockchain": "ethereum_testnet",
        "tx_hash": "0xabcdef...",
        "participants": ["red_team", "blue_team", "purple_team"]
    }
)
```

## Security Considerations

### Tamper Evidence

The Merkle chain ensures that:
1. **Any modification** to a past entry will break the chain
2. **Any deletion** of entries will be detectable
3. **Any insertion** of entries will be detectable
4. The `verify_chain()` method can detect all tampering

### Best Practices

1. **Regular Anchoring**: Anchor the chain state periodically (e.g., daily, after major incidents)
2. **External Storage**: Store anchor proofs in a separate, secure location
3. **Access Control**: Restrict write access to the audit log system only
4. **Monitoring**: Monitor the audit log files for unauthorized access attempts
5. **Backup**: Maintain encrypted backups of both log files and anchor records

### Limitations

1. **Deletion Protection**: While tampering is detectable, physical deletion of the entire log file is not prevented by the chain itself. Use filesystem protections (immutable flags, append-only mode).
2. **Real-time Verification**: Chain verification requires reading the entire log. For large logs, this may be time-consuming.
3. **Trust Assumption**: The system assumes the initial (genesis) state is trusted.

## Anchoring Process

### 1. Local Anchoring (Basic)

```python
# Simple timestamp-based anchoring
audit.anchor(anchor_data={"timestamp_server": "local"})
```

### 2. Blockchain Anchoring (Recommended)

```python
# Option A: Ethereum
import web3
w3 = web3.Web3(web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_KEY'))

latest_hash = audit.get_latest_hash()
# Create transaction with hash in data field
tx = w3.eth.send_transaction({
    'to': '0xYourAnchorContract',
    'data': latest_hash
})

# Record the anchor
audit.anchor(anchor_data={
    "blockchain": "ethereum",
    "tx_hash": tx.hex(),
    "network": "mainnet"
})
```

### 3. Timestamp Authority (RFC 3161)

```python
import requests

# Get timestamp from TSA
latest_hash = audit.get_latest_hash()
response = requests.post(
    'https://timestamp.digicert.com',
    data=latest_hash.encode(),
    headers={'Content-Type': 'application/timestamp-query'}
)

# Record the anchor
audit.anchor(anchor_data={
    "authority": "DigiCert TSA",
    "signature": response.content.hex()
})
```

## File Locations

- **Log Files**: `/var/log/mac_blue_team_audit/<case_id>.log`
- **Anchor Files**: `/var/log/mac_blue_team_audit/<case_id>_anchors.json`

Note: In test environments, these paths can be overridden by monkey-patching `core.audit._LOG_DIR`.

## API Reference

### `AuditLog(case_id: str)`

Create a new audit log instance for the specified case.

**Parameters:**
- `case_id` (str): Unique identifier for the case/incident

### `record(*, case_id: str, task_id: str, event: str, details: str = "")`

Record a new audit event.

**Parameters:**
- `case_id` (str): Case identifier
- `task_id` (str): Task/operation identifier
- `event` (str): Event type/name
- `details` (str, optional): Additional event details

**Returns:** None

### `get_latest_hash() -> str`

Get the latest hash in the chain.

**Returns:** 64-character hex string (SHA-256 hash)

### `get_entries(limit: int = None) -> list`

Retrieve log entries.

**Parameters:**
- `limit` (int, optional): Number of most recent entries to return

**Returns:** List of dicts with `entry` and `hash` keys

### `get_all_entries() -> list`

Retrieve all log entries.

**Returns:** List of dicts with `entry` and `hash` keys

### `verify_chain() -> bool`

Verify the integrity of the entire chain.

**Returns:** True if chain is valid, False if tampered

### `anchor(anchor_data: dict = None) -> dict`

Anchor the current chain state.

**Parameters:**
- `anchor_data` (dict, optional): External anchoring metadata

**Returns:** Anchor record dict

### `get_anchors() -> list`

Retrieve all anchor records for this case.

**Returns:** List of anchor record dicts

## Testing

Run the test suite:

```bash
cd /home/runner/work/jigglesmccrusty/jigglesmccrusty
python3 -m pytest tests/test_audit.py -v
```

The test suite includes:
- Basic operations (create, record, retrieve)
- Merkle chain integrity
- Tamper detection
- Anchoring functionality
- Mock red-blue-purple team scenarios
- Edge cases (empty logs, large logs, etc.)

## Examples

See `tests/test_audit.py` for comprehensive usage examples, including:
- `test_record_single_entry`: Basic recording
- `test_merkle_chain_hashing`: Chain verification
- `test_verify_chain_with_tampering`: Tamper detection
- `test_anchor_chain`: Anchoring to blockchain
- `test_mock_scenario_red_blue_purple`: Full red-blue-purple team workflow

## Future Enhancements

- [ ] Distributed consensus for multi-node deployments
- [ ] Real-time chain verification with incremental updates
- [ ] Integration with SIEM platforms (Elastic, Splunk)
- [ ] Automated periodic anchoring
- [ ] Key rotation for enhanced security
- [ ] Performance optimization for large logs (indexing, pagination)
