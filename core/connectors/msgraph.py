"""
MS Graph Connector - Manages Microsoft 365 security operations via Graph API.

Provides operations for user management, session revocation, and security
configurations through the Microsoft Graph API.
"""
import logging
import httpx
from typing import Optional


logger = logging.getLogger(__name__)


class MSGraphConnector:
    """
    Manages Microsoft 365 operations using the Microsoft Graph API.
    Requires OAuth token for authentication.
    """
    
    base_url = "https://graph.microsoft.com/v1.0"

    def __init__(self, token_provider):
        """
        Initialize the MS Graph connector.
        
        Args:
            token_provider: Async callable that returns a valid OAuth token
        """
        self.token_provider = token_provider
        logger.info("MSGraphConnector initialized")

    async def call(self, payload: dict):
        """
        Execute a Microsoft Graph operation.
        
        Supported operations:
        - revoke_tokens: Revoke all sign-in sessions for a user
        
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

        logger.debug(f"MSGraphConnector executing operation: {op}")

        try:
            token = await self.token_provider()
            if not token:
                raise RuntimeError("OAuth token not available")

            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            if op == "revoke_tokens":
                return await self._revoke_tokens(payload, headers)
            else:
                raise NotImplementedError(f"Unsupported MS Graph operation: {op}")
        except Exception as e:
            logger.error(f"MS Graph operation {op} failed: {str(e)}", exc_info=True)
            raise

    async def _revoke_tokens(self, payload: dict, headers: dict) -> dict:
        """Revoke all sign-in sessions for a user."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Missing required parameter: user_id")

        url = f"{self.base_url}/users/{user_id}/revokeSignInSessions"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            
        logger.info(f"Successfully revoked all sessions for user {user_id}")
        return {
            "summary": f"Revoked all sessions for {user_id}",
            "user_id": user_id
        }
