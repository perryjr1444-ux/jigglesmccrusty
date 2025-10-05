import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path

# In the demo we generate a random key at bootstrap time.
# In production you would fetch the master key from an HSM or Vault.
_KEY_PATH = Path("/run/secrets/master_key.bin")


def _load_master_key() -> bytes:
    if not _KEY_PATH.exists():
        raise RuntimeError("Master key not found – run bootstrap.sh first")
    return _KEY_PATH.read_bytes()


_MASTER_KEY = _load_master_key()


def encrypt_payload(plaintext: bytes) -> str:
    """AES-GCM envelope encryption – returns base64-encoded ciphertext+nonce."""
    aesgcm = AESGCM(_MASTER_KEY)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_payload(b64_cipher: str) -> bytes:
    data = base64.b64decode(b64_cipher)
    nonce, ct = data[:12], data[12:]
    aesgcm = AESGCM(_MASTER_KEY)
    return aesgcm.decrypt(nonce, ct, associated_data=None)
