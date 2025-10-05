"""Identity security agent actions."""
from __future__ import annotations

from typing import Dict

from connectors.gmail import GmailAdmin
from connectors.msgraph import MSGraphAdmin


def enforce_account_controls(context: Dict[str, str]) -> Dict[str, object]:
    user = context["user"]
    gmail = GmailAdmin(token=context.get("google_token", "demo-token"))
    msgraph = MSGraphAdmin(tenant_id=context.get("tenant_id", "tenant"), token="demo")
    return {
        "gmail": gmail.enforce_forwarding_block(user),
        "msgraph": msgraph.revoke_sessions(user),
    }


def rotate_credentials(context: Dict[str, str]) -> Dict[str, object]:
    user = context["user"]
    msgraph = MSGraphAdmin(tenant_id=context.get("tenant_id", "tenant"), token="demo")
    return {
        "password_reset": msgraph.reset_password(user),
        "app_passwords": GmailAdmin(token="demo").rotate_app_passwords(user),
    }


def prune_tokens(context: Dict[str, str]) -> Dict[str, object]:
    return {
        "user": context["user"],
        "action": "prune_tokens",
        "revoked_tokens": context.get("token_count", 0),
    }
