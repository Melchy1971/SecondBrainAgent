from secondbrain.connectors.oauth_manager import OAuthManager, OAuthToken
from secondbrain.connectors.connector_registry import ConnectorRegistry
from secondbrain.connectors.gmail_connector import GmailConnector


def test_oauth_manager():
    manager = OAuthManager()
    manager.store("gmail", OAuthToken("token"))
    assert manager.get("gmail").access_token == "token"


def test_registry():
    registry = ConnectorRegistry()
    registry.register("gmail", GmailConnector())
    assert registry.list() == ["gmail"]
