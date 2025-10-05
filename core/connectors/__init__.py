from .gmail import GmailConnector
from .msgraph import MSGraphConnector
from .router import RouterConnector
from .evidence import EvidenceConnector


class ConnectorRegistry:
    """
    Holds instantiated connector objects keyed by the string the orchestrator
    uses (e.g. "gmail:delete_filter").
    """

    def __init__(self, token_provider):
        # token_provider is a callable that returns a fresh OAuth token for the user.
        self._registry = {
            "gmail:list_filters": GmailConnector(token_provider),
            "gmail:delete_filter": GmailConnector(token_provider),
            "gmail:change_password": GmailConnector(token_provider),
            "gmail:setup_2fa": GmailConnector(token_provider),
            "msgraph:revoke_tokens": MSGraphConnector(token_provider),
            "router:factory_reset": RouterConnector(),
            "evidence:take_snapshot": EvidenceConnector(s3_client=self._make_s3_client()),
        }

    def get(self, name: str):
        if name not in self._registry:
            raise KeyError(f"Connector {name} not registered")
        return self._registry[name]

    @staticmethod
    def _make_s3_client():
        import aiobotocore.session

        session = aiobotocore.session.get_session()
        return session.create_client(
            "s3",
            endpoint_url="http://minio:9000",
            aws_secret_access_key="minioadmin",
            aws_access_key_id="minioadmin",
            region_name="us-east-1",
        )
