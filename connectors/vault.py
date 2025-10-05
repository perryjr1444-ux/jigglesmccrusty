"""Envelope encryption using Vault/KMS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from utils.crypto import EnvelopeCipher


@dataclass
class VaultClient:
    """Wraps master key operations for secret encryption."""

    master_key: bytes

    def encrypt_secret(self, name: str, plaintext: str) -> Dict[str, str]:
        cipher = EnvelopeCipher(self.master_key)
        wrapped_key, nonce, ciphertext = cipher.encrypt(plaintext.encode("utf-8"))
        return {
            "name": name,
            "wrapped_key": wrapped_key.hex(),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
        }

    def decrypt_secret(self, wrapped_key_hex: str, nonce_hex: str, ciphertext_hex: str) -> str:
        cipher = EnvelopeCipher(self.master_key)
        plaintext = cipher.decrypt(
            bytes.fromhex(wrapped_key_hex),
            bytes.fromhex(nonce_hex),
            bytes.fromhex(ciphertext_hex),
        )
        return plaintext.decode("utf-8")
