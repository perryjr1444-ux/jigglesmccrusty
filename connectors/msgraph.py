"""Microsoft Graph helper for identity security."""
from __future__ import annotations

from typing import Dict


class MSGraphAdmin:
    def __init__(self, tenant_id: str, token: str) -> None:
        self.tenant_id = tenant_id
        self.token = token

    def reset_password(self, user: str) -> Dict[str, str]:
        return {
            "tenant": self.tenant_id,
            "user": user,
            "action": "reset_password",
            "status": "success",
        }

    def revoke_sessions(self, user: str) -> Dict[str, str]:
        return {
            "tenant": self.tenant_id,
            "user": user,
            "action": "revoke_sessions",
            "status": "completed",
        }
