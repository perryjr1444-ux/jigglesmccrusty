import hashlib
import aiofiles
from typing import List


async def sha256_file(path: str) -> str:
    """Compute SHA-256 hash of a file asynchronously."""
    h = hashlib.sha256()
    async with aiofiles.open(path, "rb") as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_string(text: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


class MerkleTree:
    """
    Build a Merkle tree from a list of data items.
    Each leaf is hashed, and parent nodes are computed by hashing
    concatenated child hashes until a single root hash remains.
    """

    def __init__(self, data_items: List[bytes]):
        """
        Initialize Merkle tree with data items.
        
        Args:
            data_items: List of byte strings to build the tree from
        """
        if not data_items:
            raise ValueError("Cannot build Merkle tree from empty data")
        
        self.leaves = [sha256_hash(item) for item in data_items]
        self.root = self._build_tree(self.leaves.copy())

    def _build_tree(self, hashes: List[str]) -> str:
        """Recursively build the Merkle tree and return root hash."""
        if len(hashes) == 1:
            return hashes[0]
        
        # If odd number of hashes, duplicate the last one
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])
        
        # Build parent level
        parent_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            parent_hash = sha256_string(combined)
            parent_hashes.append(parent_hash)
        
        return self._build_tree(parent_hashes)

    def get_root(self) -> str:
        """Return the Merkle root hash."""
        return self.root

    def get_leaves(self) -> List[str]:
        """Return the leaf hashes."""
        return self.leaves.copy()
