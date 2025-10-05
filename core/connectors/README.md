# Connectors Documentation

## Overview

Connectors are async Python classes that provide a unified interface for interacting with external services. Each connector implements a standardized `call(payload: dict)` method that accepts operation-specific parameters and returns structured results.

## Contract: `call(payload: dict)`

All connectors must implement an async `call` method with the following contract:

### Input
```python
payload: dict
```
A dictionary containing:
- `__operation` (required): String identifying the operation to perform
- Additional operation-specific parameters

### Output
```python
dict
```
A dictionary containing:
- `summary`: Human-readable description of what was accomplished
- Additional operation-specific results

### Error Handling
- `ValueError`: Raised when required parameters are missing
- `NotImplementedError`: Raised for unsupported operations
- `RuntimeError`: Raised when the operation fails
- All errors are logged with full context before being raised

## Connector Implementations

### GmailConnector

Manages Gmail security operations via Google API.

**Configuration:**
```python
from core.connectors import GmailConnector

async def token_provider():
    return "your_oauth_token"

connector = GmailConnector(token_provider)
```

**Supported Operations:**

#### list_filters
List all email filters for a user.

```python
result = await connector.call({
    "__operation": "list_filters",
    "user_id": "me"  # optional, defaults to "me"
})
# Returns: {"summary": "Found N filters", "filters": [...], "count": N}
```

#### delete_filter
Delete a specific email filter.

```python
result = await connector.call({
    "__operation": "delete_filter",
    "filter_id": "123456",
    "user_id": "me"  # optional
})
# Returns: {"summary": "Filter 123456 deleted successfully", "filter_id": "123456"}
```

#### change_password
Initiate password change flow (returns redirect URL).

```python
result = await connector.call({
    "__operation": "change_password",
    "user_id": "user@example.com"
})
# Returns: {"summary": "...", "redirect_url": "...", "instructions": "..."}
```

#### setup_2fa
Initiate 2FA setup flow (returns redirect URL).

```python
result = await connector.call({
    "__operation": "setup_2fa",
    "user_id": "user@example.com"
})
# Returns: {"summary": "...", "redirect_url": "...", "instructions": "..."}
```

---

### MSGraphConnector

Manages Microsoft 365 operations via Microsoft Graph API.

**Configuration:**
```python
from core.connectors import MSGraphConnector

async def token_provider():
    return "your_oauth_token"

connector = MSGraphConnector(token_provider)
```

**Supported Operations:**

#### revoke_tokens
Revoke all sign-in sessions for a user.

```python
result = await connector.call({
    "__operation": "revoke_tokens",
    "user_id": "user@example.com"
})
# Returns: {"summary": "Revoked all sessions for user@example.com", "user_id": "..."}
```

---

### RouterConnector

Manages network router security operations (vendor-agnostic).

**Configuration:**
```python
from core.connectors import RouterConnector

connector = RouterConnector()
```

**Supported Operations:**

#### factory_reset
Perform a factory reset on the router.

**Note:** Credentials must be encrypted using `utils.crypto.encrypt_payload()`.

```python
from utils.crypto import encrypt_payload

result = await connector.call({
    "__operation": "factory_reset",
    "router_ip": "192.168.1.1",
    "admin_user_enc": encrypt_payload(b"admin"),
    "admin_pass_enc": encrypt_payload(b"password123")
})
# Returns: {"summary": "Factory reset issued to router 192.168.1.1", "router_ip": "...", "output": "..."}
```

---

### EvidenceConnector

Manages digital evidence with cryptographic verification and chain of custody.

**Configuration:**
```python
from core.connectors import EvidenceConnector
import aiobotocore.session

session = aiobotocore.session.get_session()
s3_client = session.create_client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_secret_access_key="minioadmin",
    aws_access_key_id="minioadmin",
    region_name="us-east-1"
)

connector = EvidenceConnector(s3_client)
```

**Supported Operations:**

#### take_snapshot
Hash, upload, and record a file as evidence.

```python
result = await connector.call({
    "__operation": "take_snapshot",
    "local_path": "/path/to/evidence.log",
    "case_id": "case-001",
    "kind": "log"  # optional, defaults to "log"
})
# Returns: {
#     "artifact": {...},  # Full artifact metadata
#     "summary": "Captured log → case-001/uuid_evidence.log",
#     "sha256": "...",
#     "s3_key": "..."
# }
```

---

### VaultConnector

Manages secure credential storage using HashiCorp Vault or compatible systems.

**Configuration:**
```python
from core.connectors import VaultConnector

async def token_provider():
    return "your_vault_token"

connector = VaultConnector(
    vault_url="http://vault:8200",
    token_provider=token_provider
)
```

**Supported Operations:**

#### store_secret
Store a secret in Vault.

```python
result = await connector.call({
    "__operation": "store_secret",
    "path": "secret/myapp",
    "data": {"password": "secret123", "api_key": "xyz"}
})
# Returns: {"summary": "Secret stored at secret/myapp", "path": "secret/myapp"}
```

#### retrieve_secret
Retrieve a secret from Vault.

```python
result = await connector.call({
    "__operation": "retrieve_secret",
    "path": "secret/myapp"
})
# Returns: {
#     "summary": "Secret retrieved from secret/myapp",
#     "data": {"password": "...", "api_key": "..."},
#     "metadata": {"version": 1, ...}
# }
```

#### delete_secret
Delete a secret from Vault.

```python
result = await connector.call({
    "__operation": "delete_secret",
    "path": "secret/myapp"
})
# Returns: {"summary": "Secret deleted from secret/myapp", "path": "secret/myapp"}
```

#### list_secrets
List secrets at a path.

```python
result = await connector.call({
    "__operation": "list_secrets",
    "path": "secret/"  # optional, defaults to ""
})
# Returns: {"summary": "Found N secrets at secret/", "keys": ["secret1", "secret2", ...]}
```

---

## Testing Connectors

Each connector has comprehensive unit tests in `tests/test_connectors.py`. Run tests with:

```bash
cd ai_soc
poetry run pytest ../tests/test_connectors.py -v
```

### Test Coverage

- ✅ Gmail: 7 tests (list_filters, delete_filter, change_password, setup_2fa, error handling)
- ✅ MSGraph: 3 tests (revoke_tokens, error handling)
- ✅ Router: 3 tests (factory_reset success/failure, error handling)
- ✅ Evidence: 4 tests (take_snapshot, file validation, error handling)
- ✅ Vault: 6 tests (store/retrieve/delete/list secrets, error handling)

**Total: 23 tests, all passing**

## Security Best Practices

### 1. Credential Handling
- **Never log sensitive credentials** - all logging uses safe parameter names
- **Encrypt credentials in transit** - use `utils.crypto.encrypt_payload()` for sensitive data
- **Token providers** - use async callables to fetch fresh tokens, never store statically
- **Minimum privilege** - request only necessary OAuth scopes

### 2. Error Handling
- All operations validate required parameters before execution
- Errors include context but never expose credentials
- Failed operations are logged with full stack traces
- All errors are caught, logged, and re-raised for upstream handling

### 3. Network Security
- All HTTPS connections use certificate verification (except router operations with explicit `--insecure`)
- Timeout protection on all network calls (10-15 seconds)
- Use connection pooling via `httpx.AsyncClient` context managers

### 4. Chain of Custody (Evidence)
- All evidence captures include SHA-256 hash
- Immutable custody chain with timestamp and actor information
- S3 uploads use streaming to minimize memory footprint
- File existence validated before processing

### 5. Vault Integration
- Secrets stored with proper versioning support
- Metadata preserved for audit trails
- Token-based authentication with automatic refresh
- Support for path-based access control

## Usage Examples

### Example 1: Automated Threat Response
```python
from core.connectors import GmailConnector, MSGraphConnector

async def respond_to_phishing(user_email):
    """Respond to phishing attack by securing user account."""
    
    # Revoke all sessions
    msgraph = MSGraphConnector(token_provider)
    result1 = await msgraph.call({
        "__operation": "revoke_tokens",
        "user_id": user_email
    })
    print(result1["summary"])
    
    # Delete suspicious filters
    gmail = GmailConnector(token_provider)
    filters = await gmail.call({
        "__operation": "list_filters",
        "user_id": user_email
    })
    
    for f in filters["filters"]:
        if is_suspicious(f):
            await gmail.call({
                "__operation": "delete_filter",
                "filter_id": f["id"],
                "user_id": user_email
            })
```

### Example 2: Evidence Collection
```python
from core.connectors import EvidenceConnector

async def collect_evidence(case_id, log_file):
    """Collect and preserve evidence with chain of custody."""
    
    evidence = EvidenceConnector(s3_client)
    result = await evidence.call({
        "__operation": "take_snapshot",
        "local_path": log_file,
        "case_id": case_id,
        "kind": "system_log"
    })
    
    print(f"Evidence captured: {result['summary']}")
    print(f"SHA-256: {result['sha256']}")
    print(f"S3 location: {result['artifact']['s3_path']}")
```

### Example 3: Secure Credential Management
```python
from core.connectors import VaultConnector

async def rotate_api_keys(service_name):
    """Rotate API keys stored in Vault."""
    
    vault = VaultConnector(vault_url, token_provider)
    
    # Retrieve old key
    old = await vault.call({
        "__operation": "retrieve_secret",
        "path": f"secret/{service_name}"
    })
    
    # Generate new key
    new_key = generate_api_key()
    
    # Store new key
    await vault.call({
        "__operation": "store_secret",
        "path": f"secret/{service_name}",
        "data": {"api_key": new_key}
    })
    
    # Return old key for revocation
    return old["data"]["api_key"]
```

## Configuration

### Environment Variables

Connectors can be configured via environment variables:

```bash
# Vault
VAULT_URL=http://vault:8200
VAULT_TOKEN=s.xxxxxxxx

# MinIO/S3 (Evidence)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1

# OAuth Tokens (Gmail, MSGraph)
# Provided by token_provider callable
```

### ConnectorRegistry

The `ConnectorRegistry` class provides a centralized way to manage connector instances:

```python
from core.connectors import ConnectorRegistry

registry = ConnectorRegistry(token_provider)

# Get a connector by name
gmail = registry.get("gmail:delete_filter")
msgraph = registry.get("msgraph:revoke_tokens")
router = registry.get("router:factory_reset")
evidence = registry.get("evidence:take_snapshot")
```

## Future Enhancements

Potential additions to the connector suite:

1. **SlackConnector** - Team notifications and incident response coordination
2. **JiraConnector** - Automated incident ticket creation and tracking
3. **SplunkConnector** - SIEM integration for log analysis
4. **Active Directory Connector** - Enterprise user management
5. **Azure Sentinel Connector** - Cloud SIEM integration
6. **PagerDuty Connector** - Incident escalation and on-call management

## Contributing

When adding new connectors:

1. Implement the `call(payload: dict)` interface
2. Add comprehensive error handling with logging
3. Write unit tests with >80% coverage
4. Document all operations and parameters
5. Review for security vulnerabilities
6. Add usage examples to this README
