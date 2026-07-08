from .store import ConnectorStore
from .registry import ConnectorRegistry
from .oauth import OAuthRuntime
from .delta import DeltaSyncEngine
from .webhooks import WebhookInbox
from .providers.gmail import GmailConnector
from .providers.google_calendar import GoogleCalendarConnector
from .providers.github import GitHubConnector
from .providers.paperless import PaperlessConnector


PROVIDERS = {
    "gmail": GmailConnector,
    "google_calendar": GoogleCalendarConnector,
    "github": GitHubConnector,
    "paperless": PaperlessConnector,
}


class ConnectorRuntimeV13:
    def __init__(self, root="."):
        self.store = ConnectorStore(root)
        self.registry = ConnectorRegistry(self.store)
        self.oauth = OAuthRuntime(self.store)
        self.delta = DeltaSyncEngine(self.store)
        self.webhooks = WebhookInbox(self.store)

    def status(self) -> dict:
        connectors = self.registry.connectors()
        return {
            "connectors": len(connectors),
            "enabled": len([c for c in connectors if c.get("enabled")]),
            "tokens": len(self.oauth.tokens()),
            "webhooks_pending": len(self.webhooks.list()),
            "sync_runs": len(self.delta.runs(100000)),
        }

    def sync(self, connector_id: str) -> dict:
        connector = next((c for c in self.registry.connectors() if c["id"] == connector_id), None)
        if not connector:
            return {"ok": False, "error": "connector_not_found"}
        if not connector.get("enabled"):
            return {"ok": False, "error": "connector_disabled"}
        provider_cls = PROVIDERS.get(connector_id)
        if not provider_cls:
            return {"ok": False, "error": "provider_not_implemented"}
        cursor = self.delta.cursor(connector_id).get("cursor")
        items = provider_cls().fetch_delta(cursor)
        run = self.delta.sync_result(connector_id, items)
        return {"ok": True, "run": run, "items": items}

    def sync_all(self) -> list[dict]:
        return [self.sync(c["id"]) for c in self.registry.enabled()]
