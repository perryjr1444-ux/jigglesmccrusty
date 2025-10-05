"""
Vault Connector - Manages secure credential storage and retrieval.

This connector provides a unified interface to HashiCorp Vault or similar
secret management systems for storing and retrieving sensitive credentials
used by other connectors.
"""
import logging
import httpx
from typing import Optional


logger = logging.getLogger(__name__)


class VaultConnector:
    """
    Manages secret storage and retrieval using HashiCorp Vault API.
    Supports basic KV operations for credential management.
    """

    def __init__(self, vault_url: str = "http://vault:8200", token_provider=None):
        """
        Initialize the Vault connector.
        
        Args:
            vault_url: Base URL for the Vault service
            token_provider: Callable that returns a Vault authentication token
        """
        self.vault_url = vault_url.rstrip("/")
        self.token_provider = token_provider
        logger.info(f"VaultConnector initialized with URL: {self.vault_url}")

    async def call(self, payload: dict):
        """
        Execute a Vault operation.
        
        Supported operations:
        - store_secret: Store a secret in Vault
        - retrieve_secret: Retrieve a secret from Vault
        - delete_secret: Delete a secret from Vault
        - list_secrets: List secrets at a path
        
        Args:
            payload: Dictionary containing:
                - __operation: The operation to perform
                - Additional operation-specific parameters
                
        Returns:
            Dictionary with operation results
            
        Raises:
            NotImplementedError: If operation is not supported
            ValueError: If required parameters are missing
            RuntimeError: If the operation fails
        """
        op = payload.get("__operation")
        if not op:
            raise ValueError("Missing required parameter: __operation")

        logger.debug(f"VaultConnector executing operation: {op}")

        try:
            if op == "store_secret":
                return await self._store_secret(payload)
            elif op == "retrieve_secret":
                return await self._retrieve_secret(payload)
            elif op == "delete_secret":
                return await self._delete_secret(payload)
            elif op == "list_secrets":
                return await self._list_secrets(payload)
            else:
                raise NotImplementedError(f"Unsupported Vault operation: {op}")
        except Exception as e:
            logger.error(f"Vault operation {op} failed: {str(e)}", exc_info=True)
            raise

    async def _store_secret(self, payload: dict) -> dict:
        """Store a secret in Vault."""
        path = payload.get("path")
        secret_data = payload.get("data")
        
        if not path or not secret_data:
            raise ValueError("Missing required parameters: path and data")

        token = await self.token_provider() if self.token_provider else None
        if not token:
            raise RuntimeError("Vault token not available")

        url = f"{self.vault_url}/v1/secret/data/{path}"
        headers = {"X-Vault-Token": token, "Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"data": secret_data}, headers=headers)
            resp.raise_for_status()
            
        logger.info(f"Successfully stored secret at path: {path}")
        return {"summary": f"Secret stored at {path}", "path": path}

    async def _retrieve_secret(self, payload: dict) -> dict:
        """Retrieve a secret from Vault."""
        path = payload.get("path")
        
        if not path:
            raise ValueError("Missing required parameter: path")

        token = await self.token_provider() if self.token_provider else None
        if not token:
            raise RuntimeError("Vault token not available")

        url = f"{self.vault_url}/v1/secret/data/{path}"
        headers = {"X-Vault-Token": token}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
        logger.info(f"Successfully retrieved secret from path: {path}")
        return {
            "summary": f"Secret retrieved from {path}",
            "data": data.get("data", {}).get("data", {}),
            "metadata": data.get("data", {}).get("metadata", {})
        }

    async def _delete_secret(self, payload: dict) -> dict:
        """Delete a secret from Vault."""
        path = payload.get("path")
        
        if not path:
            raise ValueError("Missing required parameter: path")

        token = await self.token_provider() if self.token_provider else None
        if not token:
            raise RuntimeError("Vault token not available")

        url = f"{self.vault_url}/v1/secret/data/{path}"
        headers = {"X-Vault-Token": token}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=headers)
            resp.raise_for_status()
            
        logger.info(f"Successfully deleted secret at path: {path}")
        return {"summary": f"Secret deleted from {path}", "path": path}

    async def _list_secrets(self, payload: dict) -> dict:
        """List secrets at a path."""
        path = payload.get("path", "")
        
        token = await self.token_provider() if self.token_provider else None
        if not token:
            raise RuntimeError("Vault token not available")

        url = f"{self.vault_url}/v1/secret/metadata/{path}"
        headers = {"X-Vault-Token": token}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request("LIST", url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
        keys = data.get("data", {}).get("keys", [])
        logger.info(f"Successfully listed {len(keys)} secrets at path: {path}")
        return {"summary": f"Found {len(keys)} secrets at {path}", "keys": keys}
