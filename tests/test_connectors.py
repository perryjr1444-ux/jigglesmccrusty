"""
Unit tests for connector implementations.

Tests each connector's call interface, error handling, and operation logic.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import sys
import pathlib

# Add core to path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.connectors.gmail import GmailConnector
from core.connectors.msgraph import MSGraphConnector
from core.connectors.router import RouterConnector
from core.connectors.evidence import EvidenceConnector
from core.connectors.vault import VaultConnector


class TestGmailConnector:
    """Test suite for Gmail connector operations."""

    @pytest.fixture
    def mock_token_provider(self):
        """Create a mock token provider."""
        async def provider():
            return "mock_oauth_token"
        return provider

    @pytest.fixture
    def connector(self, mock_token_provider):
        """Create a Gmail connector instance."""
        return GmailConnector(mock_token_provider)

    @pytest.mark.asyncio
    async def test_list_filters_success(self, connector):
        """Test successful filter listing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "filter": [
                {"id": "1", "criteria": {"from": "test@example.com"}},
                {"id": "2", "criteria": {"subject": "spam"}}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "list_filters",
                "user_id": "me"
            })
            
            assert result["count"] == 2
            assert len(result["filters"]) == 2
            assert "Found 2 filters" in result["summary"]

    @pytest.mark.asyncio
    async def test_delete_filter_success(self, connector):
        """Test successful filter deletion."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "delete_filter",
                "filter_id": "123",
                "user_id": "me"
            })
            
            assert result["filter_id"] == "123"
            assert "deleted successfully" in result["summary"]

    @pytest.mark.asyncio
    async def test_delete_filter_missing_id(self, connector):
        """Test filter deletion with missing filter_id."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({
                "__operation": "delete_filter",
                "user_id": "me"
            })
        assert "filter_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_change_password(self, connector):
        """Test password change flow initiation."""
        result = await connector.call({
            "__operation": "change_password",
            "user_id": "test@example.com"
        })
        
        assert "redirect_url" in result
        assert "password" in result["redirect_url"].lower()
        assert "instructions" in result

    @pytest.mark.asyncio
    async def test_setup_2fa(self, connector):
        """Test 2FA setup flow initiation."""
        result = await connector.call({
            "__operation": "setup_2fa",
            "user_id": "test@example.com"
        })
        
        assert "redirect_url" in result
        assert "two-step" in result["redirect_url"]
        assert "instructions" in result

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, connector):
        """Test handling of unsupported operations."""
        with pytest.raises(NotImplementedError) as exc_info:
            await connector.call({
                "__operation": "unsupported_op"
            })
        assert "unsupported_op" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_missing_operation(self, connector):
        """Test handling of missing operation parameter."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({})
        assert "__operation" in str(exc_info.value)


class TestMSGraphConnector:
    """Test suite for MS Graph connector operations."""

    @pytest.fixture
    def mock_token_provider(self):
        """Create a mock token provider."""
        async def provider():
            return "mock_oauth_token"
        return provider

    @pytest.fixture
    def connector(self, mock_token_provider):
        """Create an MS Graph connector instance."""
        return MSGraphConnector(mock_token_provider)

    @pytest.mark.asyncio
    async def test_revoke_tokens_success(self, connector):
        """Test successful token revocation."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "revoke_tokens",
                "user_id": "user@example.com"
            })
            
            assert result["user_id"] == "user@example.com"
            assert "Revoked all sessions" in result["summary"]

    @pytest.mark.asyncio
    async def test_revoke_tokens_missing_user_id(self, connector):
        """Test token revocation with missing user_id."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({
                "__operation": "revoke_tokens"
            })
        assert "user_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, connector):
        """Test handling of unsupported operations."""
        with pytest.raises(NotImplementedError) as exc_info:
            await connector.call({
                "__operation": "unsupported_op"
            })
        assert "unsupported_op" in str(exc_info.value).lower()


class TestRouterConnector:
    """Test suite for Router connector operations."""

    @pytest.fixture
    def connector(self):
        """Create a Router connector instance."""
        return RouterConnector()

    @pytest.mark.asyncio
    async def test_factory_reset_success(self, connector):
        """Test successful router factory reset."""
        # Mock the entire crypto module before it's imported
        mock_crypto = MagicMock()
        mock_crypto.decrypt_payload.side_effect = [b"admin", b"password123"]
        
        with patch.dict("sys.modules", {"utils.crypto": mock_crypto}):
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"Reset successful", b""))
            mock_proc.returncode = 0
            
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await connector.call({
                    "__operation": "factory_reset",
                    "router_ip": "192.168.1.1",
                    "admin_user_enc": "encrypted_user",
                    "admin_pass_enc": "encrypted_pass"
                })
                
                assert result["router_ip"] == "192.168.1.1"
                assert "Factory reset issued" in result["summary"]

    @pytest.mark.asyncio
    async def test_factory_reset_missing_params(self, connector):
        """Test factory reset with missing parameters."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({
                "__operation": "factory_reset",
                "router_ip": "192.168.1.1"
            })
        assert "admin_user_enc" in str(exc_info.value) or "admin_pass_enc" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_factory_reset_command_failure(self, connector):
        """Test factory reset with command failure."""
        # Mock the entire crypto module before it's imported
        mock_crypto = MagicMock()
        mock_crypto.decrypt_payload.side_effect = [b"admin", b"password123"]
        
        with patch.dict("sys.modules", {"utils.crypto": mock_crypto}):
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b"Connection failed"))
            mock_proc.returncode = 1
            
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(RuntimeError) as exc_info:
                    await connector.call({
                        "__operation": "factory_reset",
                        "router_ip": "192.168.1.1",
                        "admin_user_enc": "encrypted_user",
                        "admin_pass_enc": "encrypted_pass"
                    })
                assert "failed" in str(exc_info.value).lower()


class TestEvidenceConnector:
    """Test suite for Evidence connector operations."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        client = MagicMock()
        client.put_object = AsyncMock()
        return client

    @pytest.fixture
    def connector(self, mock_s3_client):
        """Create an Evidence connector instance."""
        return EvidenceConnector(mock_s3_client)

    @pytest.mark.asyncio
    async def test_take_snapshot_success(self, connector, tmp_path):
        """Test successful evidence snapshot."""
        # Create a temporary test file
        test_file = tmp_path / "evidence.log"
        test_file.write_text("evidence data")

        # Create an async mock for aiofiles.open
        mock_file = AsyncMock()
        mock_file.__aenter__.return_value = mock_file
        mock_file.__aexit__.return_value = None
        
        # Mock sha256_file to return a hash directly
        async def mock_sha256(path):
            return "abc123hash"

        with patch("core.connectors.evidence.sha256_file", side_effect=mock_sha256):
            with patch("core.connectors.evidence.aiofiles.open", return_value=mock_file):
                with patch("core.connectors.evidence.os.path.exists", return_value=True):
                    result = await connector.call({
                        "__operation": "take_snapshot",
                        "local_path": str(test_file),
                        "case_id": "case-001",
                        "kind": "log"
                    })
                    
                    assert "artifact" in result
                    assert result["artifact"]["case_id"] == "case-001"
                    assert result["artifact"]["sha256"] == "abc123hash"
                    assert "Captured log" in result["summary"]

    @pytest.mark.asyncio
    async def test_take_snapshot_missing_params(self, connector):
        """Test snapshot with missing parameters."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({
                "__operation": "take_snapshot",
                "local_path": "/tmp/test.log"
            })
        assert "case_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_take_snapshot_file_not_found(self, connector):
        """Test snapshot with non-existent file."""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                await connector.call({
                    "__operation": "take_snapshot",
                    "local_path": "/nonexistent/file.log",
                    "case_id": "case-001"
                })

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, connector):
        """Test handling of unsupported operations."""
        with pytest.raises(NotImplementedError) as exc_info:
            await connector.call({
                "__operation": "unsupported_op"
            })
        assert "unsupported_op" in str(exc_info.value).lower()


class TestVaultConnector:
    """Test suite for Vault connector operations."""

    @pytest.fixture
    def mock_token_provider(self):
        """Create a mock token provider."""
        async def provider():
            return "mock_vault_token"
        return provider

    @pytest.fixture
    def connector(self, mock_token_provider):
        """Create a Vault connector instance."""
        return VaultConnector("http://vault:8200", mock_token_provider)

    @pytest.mark.asyncio
    async def test_store_secret_success(self, connector):
        """Test successful secret storage."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "store_secret",
                "path": "secret/myapp",
                "data": {"password": "secret123"}
            })
            
            assert result["path"] == "secret/myapp"
            assert "stored" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_retrieve_secret_success(self, connector):
        """Test successful secret retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "data": {"password": "secret123"},
                "metadata": {"version": 1}
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "retrieve_secret",
                "path": "secret/myapp"
            })
            
            assert result["data"]["password"] == "secret123"
            assert "retrieved" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_delete_secret_success(self, connector):
        """Test successful secret deletion."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.delete = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "delete_secret",
                "path": "secret/myapp"
            })
            
            assert result["path"] == "secret/myapp"
            assert "deleted" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_list_secrets_success(self, connector):
        """Test successful secret listing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "keys": ["secret1", "secret2", "secret3"]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await connector.call({
                "__operation": "list_secrets",
                "path": "secret/"
            })
            
            assert len(result["keys"]) == 3
            assert "Found 3 secrets" in result["summary"]

    @pytest.mark.asyncio
    async def test_store_secret_missing_params(self, connector):
        """Test secret storage with missing parameters."""
        with pytest.raises(ValueError) as exc_info:
            await connector.call({
                "__operation": "store_secret",
                "path": "secret/myapp"
            })
        assert "data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, connector):
        """Test handling of unsupported operations."""
        with pytest.raises(NotImplementedError) as exc_info:
            await connector.call({
                "__operation": "unsupported_op"
            })
        assert "unsupported_op" in str(exc_info.value).lower()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
