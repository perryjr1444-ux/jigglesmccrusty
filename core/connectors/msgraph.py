import httpx


class MSGraphConnector:
    base_url = "https://graph.microsoft.com/v1.0"

    def __init__(self, token_provider):
        self.token_provider = token_provider

    async def call(self, payload: dict):
        op = payload["__operation"]
        token = await self.token_provider()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        if op == "revoke_tokens":
            user_id = payload["user_id"]
            url = f"{self.base_url}/users/{user_id}/revokeSignInSessions"
            resp = await httpx.post(url, headers=headers, timeout=15.0)
            resp.raise_for_status()
            return {"summary": f"Revoked all sessions for {user_id}"}

        raise NotImplementedError(f"Unsupported MS Graph op {op}")
