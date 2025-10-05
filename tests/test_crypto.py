"""Unit tests for the crypto utilities."""
import sys
import pathlib
import tempfile
import base64

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Mock the master key path for testing
from utils import crypto

# Create a temporary master key for testing
_test_key = None


def setup_test_key():
    """Create a temporary master key for testing."""
    global _test_key
    _test_key = AESGCM.generate_key(bit_length=256)
    # Override the module-level key
    crypto._MASTER_KEY = _test_key


def test_generate_key():
    """Test key generation."""
    key = crypto.generate_key()
    assert len(key) == 32  # 256 bits = 32 bytes
    
    # Generate another key, should be different
    key2 = crypto.generate_key()
    assert key != key2


def test_encrypt_decrypt_payload():
    """Test basic encryption and decryption."""
    setup_test_key()
    
    plaintext = b"Secret message"
    encrypted = crypto.encrypt_payload(plaintext)
    
    # Verify it's base64 encoded
    assert isinstance(encrypted, str)
    decoded = base64.b64decode(encrypted)
    assert len(decoded) > len(plaintext)  # Includes nonce and tag
    
    # Decrypt and verify
    decrypted = crypto.decrypt_payload(encrypted)
    assert decrypted == plaintext


def test_encrypt_decrypt_with_custom_key():
    """Test encryption and decryption with a custom key."""
    custom_key = crypto.generate_key()
    
    plaintext = b"Secret message with custom key"
    encrypted = crypto.encrypt_payload(plaintext, key=custom_key)
    decrypted = crypto.decrypt_payload(encrypted, key=custom_key)
    
    assert decrypted == plaintext


def test_decrypt_wrong_key_fails():
    """Test that decryption with wrong key fails."""
    key1 = crypto.generate_key()
    key2 = crypto.generate_key()
    
    plaintext = b"Secret message"
    encrypted = crypto.encrypt_payload(plaintext, key=key1)
    
    # Try to decrypt with wrong key
    with pytest.raises(ValueError, match="Decryption failed"):
        crypto.decrypt_payload(encrypted, key=key2)


def test_encrypt_string():
    """Test string encryption."""
    setup_test_key()
    
    plaintext = "Hello, World!"
    encrypted = crypto.encrypt_string(plaintext)
    
    assert isinstance(encrypted, str)
    assert plaintext not in encrypted


def test_decrypt_string():
    """Test string decryption."""
    setup_test_key()
    
    plaintext = "Hello, World!"
    encrypted = crypto.encrypt_string(plaintext)
    decrypted = crypto.decrypt_string(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_decrypt_empty_string():
    """Test encrypting and decrypting an empty string."""
    setup_test_key()
    
    plaintext = ""
    encrypted = crypto.encrypt_string(plaintext)
    decrypted = crypto.decrypt_string(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_decrypt_unicode():
    """Test encrypting and decrypting Unicode strings."""
    setup_test_key()
    
    plaintext = "Hello 世界! 🔐"
    encrypted = crypto.encrypt_string(plaintext)
    decrypted = crypto.decrypt_string(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_decrypt_large_payload():
    """Test encrypting and decrypting a large payload."""
    setup_test_key()
    
    plaintext = b"A" * 100000  # 100KB
    encrypted = crypto.encrypt_payload(plaintext)
    decrypted = crypto.decrypt_payload(encrypted)
    
    assert decrypted == plaintext


def test_encryption_produces_different_ciphertext():
    """Test that encrypting the same plaintext produces different ciphertext."""
    setup_test_key()
    
    plaintext = b"Same message"
    encrypted1 = crypto.encrypt_payload(plaintext)
    encrypted2 = crypto.encrypt_payload(plaintext)
    
    # Different because of random nonce
    assert encrypted1 != encrypted2
    
    # But both decrypt to same plaintext
    assert crypto.decrypt_payload(encrypted1) == plaintext
    assert crypto.decrypt_payload(encrypted2) == plaintext


def test_decrypt_invalid_base64():
    """Test that invalid base64 raises an error."""
    setup_test_key()
    
    with pytest.raises(ValueError, match="Decryption failed"):
        crypto.decrypt_payload("not valid base64!!!")


def test_decrypt_too_short():
    """Test that too-short ciphertext raises an error."""
    setup_test_key()
    
    # Create a valid base64 string but too short to contain nonce
    short_data = base64.b64encode(b"short").decode()
    
    with pytest.raises(ValueError, match="Invalid ciphertext: too short"):
        crypto.decrypt_payload(short_data)


def test_decrypt_corrupted_ciphertext():
    """Test that corrupted ciphertext raises an error."""
    setup_test_key()
    
    plaintext = b"Secret message"
    encrypted = crypto.encrypt_payload(plaintext)
    
    # Corrupt the ciphertext
    decoded = base64.b64decode(encrypted)
    corrupted = decoded[:-1] + b'X'  # Change last byte
    corrupted_b64 = base64.b64encode(corrupted).decode()
    
    with pytest.raises(ValueError, match="Decryption failed"):
        crypto.decrypt_payload(corrupted_b64)


def test_encrypt_payload_with_empty_bytes():
    """Test encrypting empty bytes."""
    setup_test_key()
    
    plaintext = b""
    encrypted = crypto.encrypt_payload(plaintext)
    decrypted = crypto.decrypt_payload(encrypted)
    
    assert decrypted == plaintext


def test_string_encryption_with_custom_key():
    """Test string encryption with custom key."""
    custom_key = crypto.generate_key()
    
    plaintext = "Custom key message"
    encrypted = crypto.encrypt_string(plaintext, key=custom_key)
    decrypted = crypto.decrypt_string(encrypted, key=custom_key)
    
    assert decrypted == plaintext


def test_nonce_is_included():
    """Test that the nonce is included in the encrypted output."""
    setup_test_key()
    
    plaintext = b"Test message"
    encrypted = crypto.encrypt_payload(plaintext)
    
    # Decode and check that first 12 bytes are the nonce
    decoded = base64.b64decode(encrypted)
    assert len(decoded) >= 12  # At least nonce + some ciphertext
