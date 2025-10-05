"""Envelope encryption wrapper using AES-GCM."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class EnvelopeCipher:
    """Encrypts data with a randomly generated data key wrapped by a master key."""

    master_key: bytes

    def generate_data_key(self) -> bytes:
        return os.urandom(32)

    def encrypt(self, plaintext: bytes, associated_data: bytes | None = None) -> Tuple[bytes, bytes, bytes]:
        data_key = self.generate_data_key()
        aesgcm = AESGCM(data_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        wrapped_key = AESGCM(self.master_key).encrypt(nonce, data_key, associated_data)
        return wrapped_key, nonce, ciphertext

    def decrypt(self, wrapped_key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
        data_key = AESGCM(self.master_key).decrypt(nonce, wrapped_key, associated_data)
        aesgcm = AESGCM(data_key)
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
