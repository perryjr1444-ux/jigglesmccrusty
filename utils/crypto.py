import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path
from typing import Optional

# In the demo we generate a random key at bootstrap time.
# In production you would fetch the master key from an HSM or Vault.
_KEY_PATH = Path("/run/secrets/master_key.bin")
_MASTER_KEY: Optional[bytes] = None


def _load_master_key() -> bytes:
    """Load the master encryption key from the key path."""
    if not _KEY_PATH.exists():
        raise RuntimeError("Master key not found – run bootstrap.sh first")
    return _KEY_PATH.read_bytes()


def _get_master_key() -> bytes:
    """Get the master key, loading it if necessary."""
    global _MASTER_KEY
    if _MASTER_KEY is None:
        _MASTER_KEY = _load_master_key()
    return _MASTER_KEY


def generate_key() -> bytes:
    """
    Generate a new 256-bit AES key.
    
    Returns:
        32 bytes suitable for AES-256
    """
    return AESGCM.generate_key(bit_length=256)


def encrypt_payload(plaintext: bytes, key: Optional[bytes] = None) -> str:
    """
    AES-GCM envelope encryption – returns base64-encoded ciphertext+nonce.
    
    Args:
        plaintext: The data to encrypt
        key: Optional key to use (defaults to master key)
    
    Returns:
        Base64-encoded string containing nonce+ciphertext
    """
    encryption_key = key if key is not None else _get_master_key()
    aesgcm = AESGCM(encryption_key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_payload(b64_cipher: str, key: Optional[bytes] = None) -> bytes:
    """
    Decrypt AES-GCM encrypted payload.
    
    Args:
        b64_cipher: Base64-encoded nonce+ciphertext
        key: Optional key to use (defaults to master key)
    
    Returns:
        Decrypted plaintext bytes
    
    Raises:
        ValueError: If decryption fails (wrong key or corrupted data)
    """
    try:
        data = base64.b64decode(b64_cipher)
        if len(data) < 12:
            raise ValueError("Invalid ciphertext: too short")
        
        nonce, ct = data[:12], data[12:]
        decryption_key = key if key is not None else _get_master_key()
        aesgcm = AESGCM(decryption_key)
        return aesgcm.decrypt(nonce, ct, associated_data=None)
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def encrypt_string(plaintext: str, key: Optional[bytes] = None) -> str:
    """
    Encrypt a string using AES-GCM.
    
    Args:
        plaintext: The string to encrypt
        key: Optional key to use (defaults to master key)
    
    Returns:
        Base64-encoded encrypted string
    """
    return encrypt_payload(plaintext.encode('utf-8'), key)


def decrypt_string(b64_cipher: str, key: Optional[bytes] = None) -> str:
    """
    Decrypt a string using AES-GCM.
    
    Args:
        b64_cipher: Base64-encoded encrypted string
        key: Optional key to use (defaults to master key)
    
    Returns:
        Decrypted string
    """
    return decrypt_payload(b64_cipher, key).decode('utf-8')
