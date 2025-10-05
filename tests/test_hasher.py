"""Unit tests for the hasher and Merkle tree utilities."""
import sys
import pathlib
import tempfile
import asyncio

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from utils.hasher import sha256_file, sha256_hash, sha256_string, MerkleTree


def test_sha256_hash():
    """Test SHA-256 hashing of bytes."""
    data = b"Hello, World!"
    hash_result = sha256_hash(data)
    
    # Known SHA-256 hash for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert hash_result == expected


def test_sha256_string():
    """Test SHA-256 hashing of strings."""
    text = "Hello, World!"
    hash_result = sha256_string(text)
    
    # Should be same as hashing the bytes
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert hash_result == expected


def test_sha256_hash_empty():
    """Test SHA-256 hashing of empty data."""
    hash_result = sha256_hash(b"")
    
    # Known SHA-256 hash for empty string
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert hash_result == expected


@pytest.mark.asyncio
async def test_sha256_file():
    """Test SHA-256 hashing of a file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash_result = await sha256_file(temp_path)
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_result == expected
    finally:
        pathlib.Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_sha256_file_large():
    """Test SHA-256 hashing of a larger file."""
    # Create a temporary file with multiple chunks
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        # Write more than one 8192-byte chunk
        f.write(b"A" * 10000)
        temp_path = f.name
    
    try:
        hash_result = await sha256_file(temp_path)
        # Just verify it returns a valid hash (64 hex chars)
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
    finally:
        pathlib.Path(temp_path).unlink()


def test_merkle_tree_single_item():
    """Test Merkle tree with a single item."""
    data = [b"single item"]
    tree = MerkleTree(data)
    
    root = tree.get_root()
    leaves = tree.get_leaves()
    
    assert len(leaves) == 1
    assert root == sha256_hash(b"single item")


def test_merkle_tree_two_items():
    """Test Merkle tree with two items."""
    data = [b"item1", b"item2"]
    tree = MerkleTree(data)
    
    root = tree.get_root()
    leaves = tree.get_leaves()
    
    assert len(leaves) == 2
    # Root should be hash of concatenated leaf hashes
    leaf1 = sha256_hash(b"item1")
    leaf2 = sha256_hash(b"item2")
    expected_root = sha256_string(leaf1 + leaf2)
    assert root == expected_root


def test_merkle_tree_four_items():
    """Test Merkle tree with four items (perfect binary tree)."""
    data = [b"item1", b"item2", b"item3", b"item4"]
    tree = MerkleTree(data)
    
    root = tree.get_root()
    leaves = tree.get_leaves()
    
    assert len(leaves) == 4
    assert len(root) == 64  # SHA-256 produces 64 hex chars


def test_merkle_tree_odd_items():
    """Test Merkle tree with odd number of items."""
    data = [b"item1", b"item2", b"item3"]
    tree = MerkleTree(data)
    
    root = tree.get_root()
    leaves = tree.get_leaves()
    
    # Leaves should contain original 3 items
    assert len(leaves) == 3
    assert len(root) == 64


def test_merkle_tree_deterministic():
    """Test that Merkle tree is deterministic."""
    data = [b"item1", b"item2", b"item3"]
    
    tree1 = MerkleTree(data)
    tree2 = MerkleTree(data)
    
    assert tree1.get_root() == tree2.get_root()
    assert tree1.get_leaves() == tree2.get_leaves()


def test_merkle_tree_different_order():
    """Test that different order produces different root."""
    data1 = [b"item1", b"item2"]
    data2 = [b"item2", b"item1"]
    
    tree1 = MerkleTree(data1)
    tree2 = MerkleTree(data2)
    
    assert tree1.get_root() != tree2.get_root()


def test_merkle_tree_empty_raises():
    """Test that empty data list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot build Merkle tree from empty data"):
        MerkleTree([])


def test_merkle_tree_get_leaves_copy():
    """Test that get_leaves returns a copy, not the original."""
    data = [b"item1", b"item2"]
    tree = MerkleTree(data)
    
    leaves1 = tree.get_leaves()
    leaves2 = tree.get_leaves()
    
    # Should be equal but not the same object
    assert leaves1 == leaves2
    assert leaves1 is not leaves2


def test_merkle_tree_many_items():
    """Test Merkle tree with many items."""
    # Test with 100 items
    data = [f"item{i}".encode() for i in range(100)]
    tree = MerkleTree(data)
    
    root = tree.get_root()
    leaves = tree.get_leaves()
    
    assert len(leaves) == 100
    assert len(root) == 64


def test_merkle_tree_string_content():
    """Test Merkle tree with various string content."""
    data = [
        b"transaction1",
        b"transaction2",
        b"transaction3",
        b"transaction4",
    ]
    tree = MerkleTree(data)
    
    # Verify root is consistent
    root1 = tree.get_root()
    tree2 = MerkleTree(data)
    root2 = tree2.get_root()
    
    assert root1 == root2
