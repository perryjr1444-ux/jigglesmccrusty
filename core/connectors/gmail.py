"""
Gmail Connector - Manages Gmail security operations via Google API.

Provides operations for managing filters, password changes, and 2FA setup
through the Gmail/Google API.
"""
import logging
import httpx
from typing import Optional


logger = logging.getLogger(__name__)


class GmailConnector:
    """
    Manages Gmail security operations using the Gmail API.
    Requires OAuth token for authentication.
    """
    
    base_url = "https://gmail.googleapis.com/gmail/v1"
    accounts_url = "https://accounts.google.com"

    def __init__(self, token_provider):
        """
        Initialize the Gmail connector.
        
        Args:
            token_provider: Async callable that returns a valid OAuth token
        """
        self.token_provider = token_provider
        logger.info("GmailConnector initialized")

    async def call(self, payload: dict):
        """
        Execute a Gmail operation.
        
        Supported operations:
        - list_filters: List all email filters
        - delete_filter: Delete a specific filter
        - change_password: Initiate password change flow
        - setup_2fa: Enable two-factor authentication
        
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

        logger.debug(f"GmailConnector executing operation: {op}")

        try:
            if op == "list_filters":
                return await self._list_filters(payload)
            elif op == "delete_filter":
                return await self._delete_filter(payload)
            elif op == "change_password":
                return await self._change_password(payload)
            elif op == "setup_2fa":
                return await self._setup_2fa(payload)
            else:
                raise NotImplementedError(f"Unsupported Gmail operation: {op}")
        except Exception as e:
            logger.error(f"Gmail operation {op} failed: {str(e)}", exc_info=True)
            raise

    async def _list_filters(self, payload: dict) -> dict:
        """List all Gmail filters for the authenticated user."""
        user_id = payload.get("user_id", "me")
        
        token = await self.token_provider()
        if not token:
            raise RuntimeError("OAuth token not available")

        url = f"{self.base_url}/users/{user_id}/settings/filters"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
        filters = data.get("filter", [])
        logger.info(f"Retrieved {len(filters)} Gmail filters for user {user_id}")
        return {
            "summary": f"Found {len(filters)} filters",
            "filters": filters,
            "count": len(filters)
        }

    async def _delete_filter(self, payload: dict) -> dict:
        """Delete a specific Gmail filter."""
        filter_id = payload.get("filter_id")
        user_id = payload.get("user_id", "me")
        
        if not filter_id:
            raise ValueError("Missing required parameter: filter_id")

        token = await self.token_provider()
        if not token:
            raise RuntimeError("OAuth token not available")

        url = f"{self.base_url}/users/{user_id}/settings/filters/{filter_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.delete(url, headers=headers)
            resp.raise_for_status()
            
        logger.info(f"Successfully deleted Gmail filter {filter_id} for user {user_id}")
        return {
            "summary": f"Filter {filter_id} deleted successfully",
            "filter_id": filter_id
        }

    async def _change_password(self, payload: dict) -> dict:
        """
        Initiate password change flow for the user.
        
        Note: This returns a redirect URL as the actual password change
        must be done through Google's secure flow.
        """
        user_id = payload.get("user_id", "me")
        redirect_uri = payload.get("redirect_uri", "https://myaccount.google.com/security")
        
        token = await self.token_provider()
        if not token:
            raise RuntimeError("OAuth token not available")

        # Google doesn't provide a direct API to change passwords
        # This would redirect to the secure password change page
        password_change_url = f"https://myaccount.google.com/signinoptions/password"
        
        logger.info(f"Initiated password change flow for user {user_id}")
        return {
            "summary": "Password change initiated - user must complete via Google",
            "redirect_url": password_change_url,
            "user_id": user_id,
            "instructions": "User must complete password change through Google's secure interface"
        }

    async def _setup_2fa(self, payload: dict) -> dict:
        """
        Initiate 2FA setup flow for the user.
        
        Note: This returns a redirect URL as the actual 2FA setup
        must be done through Google's secure flow.
        """
        user_id = payload.get("user_id", "me")
        
        token = await self.token_provider()
        if not token:
            raise RuntimeError("OAuth token not available")

        # Google requires 2FA setup through their secure interface
        twofa_setup_url = "https://myaccount.google.com/signinoptions/two-step-verification"
        
        logger.info(f"Initiated 2FA setup flow for user {user_id}")
        return {
            "summary": "2FA setup initiated - user must complete via Google",
            "redirect_url": twofa_setup_url,
            "user_id": user_id,
            "instructions": "User must complete 2FA setup through Google's secure interface"
        }
