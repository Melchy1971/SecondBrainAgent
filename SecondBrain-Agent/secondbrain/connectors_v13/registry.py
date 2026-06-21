from datetime import datetime, timezone


DEFAULT_CONNECTORS = [
    {"id": "gmail", "name": "Gmail", "kind": "email", "enabled": False, "auth": "oauth2"},
    {"id": "google_calendar", "name": "Google Calendar", "kind": "calendar", "enabled": False, "auth": "oauth2"},
    {"id": "github", "name": "GitHub", "kind": "code", "enabled": False, "auth": "oauth2"},
    {"id": "paperless", "name": "Paperless-ngx", "kind": "documents", "enabled": False, "auth": "api_token"},
    {"id": "obsidian", "name": "Obsidian Vault", "kind": "files", "enabled": False, "auth": "local_path"},
]


class ConnectorRegistry:
    def __init__(self, store):
        self.store = store

    def connectors(self) -> list[dict]:
        connectors = self.store.load("connectors", None)
        if connectors is None:
            connectors = DEFAULT_CONNECTORS
            self.store.save("connectors", connectors)
        return connectors

    def set_enabled(self, connector_id: str, enabled: bool) -> dict:
        updated = []
        found = None
        for c in self.connectors():
            if c["id"] == connector_id:
                c = {**c, "enabled": enabled, "updated_at": datetime.now(timezone.utc).isoformat()}
                found = c
            updated.append(c)
        self.store.save("connectors", updated)
        return found or {"ok": False, "error": "connector_not_found", "connector_id": connector_id}

    def enabled(self) -> list[dict]:
        return [c for c in self.connectors() if c.get("enabled")]
