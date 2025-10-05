# Utility Functions Documentation

This document provides comprehensive documentation for the security and privacy utility functions available in the `utils` package.

## Table of Contents

- [Redactor (`utils/redactor.py`)](#redactor)
- [Hasher & Merkle Tree (`utils/hasher.py`)](#hasher--merkle-tree)
- [Crypto (`utils/crypto.py`)](#crypto)

---

## Redactor

The redactor module provides deterministic tokenization and redaction utilities for sensitive data.

### Functions

#### `tokenize(value: str, prefix: Optional[str] = None) -> str`

Generate a deterministic token for a given value. Same input always produces the same token.

**Parameters:**
- `value` (str): The value to tokenize
- `prefix` (str, optional): Optional prefix for the token (defaults to "TOK_")

**Returns:**
- str: A deterministic token string

**Example:**
```python
from utils.redactor import tokenize

token = tokenize("sensitive-value")
print(token)  # TOK_xYz123AbC...

# Same input produces same token
token2 = tokenize("sensitive-value")
assert token == token2

# Custom prefix
custom = tokenize("sensitive-value", prefix="SECRET_")
print(custom)  # SECRET_xYz123AbC...
```

#### `redact(text: str, patterns: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]`

Scan for email addresses, phone numbers, SSNs, and other sensitive patterns in text and replace them with deterministic tokens.

**Parameters:**
- `text` (str): The text to redact
- `patterns` (dict, optional): Custom patterns dictionary `{regex: pattern_name}`

**Returns:**
- tuple: `(redacted_text, token_map)` where `token_map` is `{token: original_value}`

**Default Patterns:**
- Email addresses
- US SSN (123-45-6789)
- Phone numbers

**Example:**
```python
from utils.redactor import redact

text = "Contact john@example.com at 555-123-4567 for details."
redacted_text, token_map = redact(text)

print(redacted_text)
# Output: "Contact TOK_abc123... at TOK_xyz789... for details."

print(token_map)
# Output: {'TOK_abc123...': 'john@example.com', 'TOK_xyz789...': '555-123-4567'}
```

**Custom Patterns Example:**
```python
text = "API key: sk_test_123456789"
patterns = {r"sk_test_\w+": "api_key"}
redacted, tokens = redact(text, patterns=patterns)
```

#### `restore(redacted_text: str, token_map: Dict[str, str]) -> str`

Restore original values from redacted text using the token map.

**Parameters:**
- `redacted_text` (str): Text containing tokens
- `token_map` (dict): Map of `{token: original_value}`

**Returns:**
- str: Text with original values restored

**Example:**
```python
from utils.redactor import redact, restore

original = "Email: support@example.com"
redacted, token_map = redact(original)
restored = restore(redacted, token_map)

assert restored == original
```

---

## Hasher & Merkle Tree

The hasher module provides SHA-256 hashing utilities and a Merkle tree implementation for integrity verification.

### Functions

#### `sha256_hash(data: bytes) -> str`

Compute SHA-256 hash of raw bytes.

**Parameters:**
- `data` (bytes): The data to hash

**Returns:**
- str: Hexadecimal hash string (64 characters)

**Example:**
```python
from utils.hasher import sha256_hash

data = b"Hello, World!"
hash_value = sha256_hash(data)
print(hash_value)  # dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
```

#### `sha256_string(text: str) -> str`

Compute SHA-256 hash of a string.

**Parameters:**
- `text` (str): The string to hash

**Returns:**
- str: Hexadecimal hash string (64 characters)

**Example:**
```python
from utils.hasher import sha256_string

hash_value = sha256_string("Hello, World!")
print(hash_value)
```

#### `async sha256_file(path: str) -> str`

Compute SHA-256 hash of a file asynchronously.

**Parameters:**
- `path` (str): Path to the file

**Returns:**
- str: Hexadecimal hash string (64 characters)

**Example:**
```python
import asyncio
from utils.hasher import sha256_file

async def hash_my_file():
    hash_value = await sha256_file("/path/to/file.txt")
    print(f"File hash: {hash_value}")

asyncio.run(hash_my_file())
```

### MerkleTree Class

Build a Merkle tree from a list of data items for efficient integrity verification.

#### `__init__(data_items: List[bytes])`

Initialize Merkle tree with data items.

**Parameters:**
- `data_items` (List[bytes]): List of byte strings to build the tree from

**Raises:**
- `ValueError`: If data_items is empty

**Example:**
```python
from utils.hasher import MerkleTree

# Create a Merkle tree from transactions
transactions = [
    b"transaction1",
    b"transaction2",
    b"transaction3",
    b"transaction4",
]

tree = MerkleTree(transactions)
root_hash = tree.get_root()
print(f"Merkle root: {root_hash}")
```

#### `get_root() -> str`

Return the Merkle root hash.

**Returns:**
- str: The root hash of the Merkle tree

#### `get_leaves() -> List[str]`

Return the leaf hashes (copies the internal list).

**Returns:**
- List[str]: List of leaf hashes

**Complete Example:**
```python
from utils.hasher import MerkleTree

# Build tree from audit log entries
entries = [
    b"entry1: user login",
    b"entry2: file access",
    b"entry3: data modification",
]

tree = MerkleTree(entries)

# Get and store the root hash for verification
root = tree.get_root()
print(f"Root hash to anchor: {root}")

# Later, rebuild tree and verify
tree2 = MerkleTree(entries)
assert tree2.get_root() == root  # Verify integrity

# Get individual leaf hashes
leaves = tree.get_leaves()
for i, leaf in enumerate(leaves):
    print(f"Entry {i} hash: {leaf}")
```

---

## Crypto

The crypto module provides AES-GCM envelope encryption and decryption utilities.

### Functions

#### `generate_key() -> bytes`

Generate a new 256-bit AES key.

**Returns:**
- bytes: 32 bytes suitable for AES-256

**Example:**
```python
from utils.crypto import generate_key

# Generate a new encryption key
key = generate_key()
print(f"Key length: {len(key)} bytes")  # 32 bytes
```

#### `encrypt_payload(plaintext: bytes, key: Optional[bytes] = None) -> str`

AES-GCM envelope encryption – returns base64-encoded ciphertext+nonce.

**Parameters:**
- `plaintext` (bytes): The data to encrypt
- `key` (bytes, optional): Optional key to use (defaults to master key)

**Returns:**
- str: Base64-encoded string containing nonce+ciphertext

**Example:**
```python
from utils.crypto import encrypt_payload

plaintext = b"Secret message"
encrypted = encrypt_payload(plaintext)
print(encrypted)  # Base64 string
```

#### `decrypt_payload(b64_cipher: str, key: Optional[bytes] = None) -> bytes`

Decrypt AES-GCM encrypted payload.

**Parameters:**
- `b64_cipher` (str): Base64-encoded nonce+ciphertext
- `key` (bytes, optional): Optional key to use (defaults to master key)

**Returns:**
- bytes: Decrypted plaintext bytes

**Raises:**
- `ValueError`: If decryption fails (wrong key or corrupted data)

**Example:**
```python
from utils.crypto import encrypt_payload, decrypt_payload

plaintext = b"Secret message"
encrypted = encrypt_payload(plaintext)
decrypted = decrypt_payload(encrypted)

assert decrypted == plaintext
```

#### `encrypt_string(plaintext: str, key: Optional[bytes] = None) -> str`

Encrypt a string using AES-GCM.

**Parameters:**
- `plaintext` (str): The string to encrypt
- `key` (bytes, optional): Optional key to use (defaults to master key)

**Returns:**
- str: Base64-encoded encrypted string

**Example:**
```python
from utils.crypto import encrypt_string, decrypt_string

message = "Hello, World! 🔐"
encrypted = encrypt_string(message)
decrypted = decrypt_string(encrypted)

assert decrypted == message
```

#### `decrypt_string(b64_cipher: str, key: Optional[bytes] = None) -> str`

Decrypt a string using AES-GCM.

**Parameters:**
- `b64_cipher` (str): Base64-encoded encrypted string
- `key` (bytes, optional): Optional key to use (defaults to master key)

**Returns:**
- str: Decrypted string

### Custom Key Example

```python
from utils.crypto import generate_key, encrypt_payload, decrypt_payload

# Generate a custom key
custom_key = generate_key()

# Encrypt with custom key
plaintext = b"Sensitive data"
encrypted = encrypt_payload(plaintext, key=custom_key)

# Decrypt with same key
decrypted = decrypt_payload(encrypted, key=custom_key)

assert decrypted == plaintext

# Using different key will fail
try:
    wrong_key = generate_key()
    decrypt_payload(encrypted, key=wrong_key)
except ValueError as e:
    print(f"Decryption failed: {e}")
```

### Complete Integration Example

```python
from utils.redactor import redact, restore
from utils.hasher import MerkleTree
from utils.crypto import encrypt_string, decrypt_string

# 1. Redact sensitive data
text = "User john@example.com accessed system from 192.168.1.1"
redacted, token_map = redact(text)

# 2. Encrypt the redacted text
encrypted = encrypt_string(redacted)

# 3. Build Merkle tree for audit trail
audit_entries = [
    encrypted.encode(),
    b"metadata: timestamp=2024-01-01",
    b"metadata: action=access",
]
tree = MerkleTree(audit_entries)
root_hash = tree.get_root()

print(f"Audit root hash: {root_hash}")

# Later: verify and restore
decrypted = decrypt_string(encrypted)
original = restore(decrypted, token_map)
print(f"Original: {original}")
```

---

## Security Considerations

### Redactor
- **Deterministic tokens**: Same value always produces the same token, which is useful for consistent redaction but means patterns can be detected
- **Token maps**: Store token maps securely as they contain the mapping back to original values
- **Custom patterns**: Be careful with regex patterns to avoid over-redacting or missing sensitive data

### Hasher
- **SHA-256**: Cryptographically secure hash function suitable for integrity verification
- **Merkle trees**: Efficient for verifying large datasets; changing any leaf invalidates the root
- **File hashing**: Uses streaming to handle large files efficiently

### Crypto
- **AES-GCM**: Authenticated encryption providing both confidentiality and integrity
- **Nonces**: Randomly generated for each encryption, ensuring different ciphertexts for same plaintext
- **Master key**: Store master key securely (HSM, Vault, etc.); never commit to source control
- **Key management**: Consider key rotation policies and secure key derivation

---

## Testing

All utilities have comprehensive unit tests:

```bash
# Run all utility tests
pytest tests/test_redactor.py tests/test_hasher.py tests/test_crypto.py -v

# Run specific test module
pytest tests/test_redactor.py -v
pytest tests/test_hasher.py -v
pytest tests/test_crypto.py -v
```

---

## Best Practices

1. **Always use tokenize/redact before logging sensitive data**
2. **Build Merkle trees for audit logs to ensure tamper-evidence**
3. **Encrypt sensitive data at rest and in transit**
4. **Store encryption keys separately from encrypted data**
5. **Use custom keys for different security domains**
6. **Regularly rotate encryption keys**
7. **Anchor Merkle roots to immutable storage for non-repudiation**
