"""Hashing helpers for audit integrity."""
from __future__ import annotations

from hashlib import sha256
from typing import Iterable, List


def digest_bytes(payload: bytes) -> str:
    """Return a hex-encoded SHA-256 digest for raw bytes."""
    return sha256(payload).hexdigest()


def digest_text(payload: str) -> str:
    """Return a hex-encoded SHA-256 digest for text using UTF-8 encoding."""
    return digest_bytes(payload.encode("utf-8"))


def merkle_root(chunks: Iterable[str]) -> str:
    """Compute a Merkle root for an iterable of hex digests.

    When the leaf count is odd we duplicate the last leaf so that every level is
    balanced. The function returns the root hash as a hexadecimal string.
    """

    layer: List[str] = list(chunks)
    if not layer:
        return digest_text("")

    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        parent: List[str] = []
        for left, right in zip(layer[0::2], layer[1::2]):
            parent.append(digest_text(left + right))
        layer = parent
    return layer[0]
