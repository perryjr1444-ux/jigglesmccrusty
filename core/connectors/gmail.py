from utils.crypto import encrypt_payload


class GmailConnector:
    def __init__(self, token_provider):
        self.token_provider = token_provider

    async def call(self, payload: dict):
        raise NotImplementedError("Gmail connector operations not implemented in this scaffold")
