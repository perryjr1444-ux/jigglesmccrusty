# Utilities Module

Security and privacy utilities for the AI SOC system.

## Quick Reference

### Redactor (`redactor.py`)
Deterministic tokenization and PII redaction.

```python
from utils.redactor import redact, restore, tokenize

# Redact sensitive data
text = "Contact john@example.com"
redacted, tokens = redact(text)

# Restore original
original = restore(redacted, tokens)
```

### Hasher (`hasher.py`)
SHA-256 hashing and Merkle tree construction.

```python
from utils.hasher import sha256_hash, MerkleTree

# Hash data
hash_value = sha256_hash(b"data")

# Build Merkle tree
tree = MerkleTree([b"item1", b"item2", b"item3"])
root = tree.get_root()
```

### Crypto (`crypto.py`)
AES-GCM envelope encryption/decryption.

```python
from utils.crypto import encrypt_string, decrypt_string, generate_key

# Encrypt data
encrypted = encrypt_string("secret message")
decrypted = decrypt_string(encrypted)

# Custom key
key = generate_key()
encrypted = encrypt_string("message", key=key)
```

## Documentation

See [docs/UTILITIES.md](../docs/UTILITIES.md) for complete documentation with examples.

## Testing

```bash
pytest tests/test_redactor.py tests/test_hasher.py tests/test_crypto.py -v
```
