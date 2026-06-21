from datetime import datetime, timezone
from uuid import uuid4
import base64


class OAuthRuntime:
    def __init__(self, store):
        self.store = store

    def templates(self) -> list[dict]:
        return [
            {"connector": "gmail", "auth_url": "https://accounts.google.com/o/oauth2/v2/auth", "scopes": ["gmail.readonly"]},
            {"connector": "google_calendar", "auth_url": "https://accounts.google.com/o/oauth2/v2/auth", "scopes": ["calendar.readonly"]},
            {"connector": "github", "auth_url": "https://github.com/login/oauth/authorize", "scopes": ["repo", "read:user"]},
            {"connector": "paperless", "auth_url": "local_api_token", "scopes": ["documents.read"]},
        ]

    def create_auth_request(self, connector_id: str, scopes: list[str]) -> dict:
        request = {
            "id": str(uuid4()),
            "connector_id": connector_id,
            "scopes": scopes,
            "state": str(uuid4()),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("oauth_requests", request)

    def store_token(self, connector_id: str, access_token: str, refresh_token: str | None = None, scopes: list[str] | None = None) -> dict:
        token = {
            "id": str(uuid4()),
            "connector_id": connector_id,
            "access_token_enc": base64.b64encode(access_token.encode()).decode(),
            "refresh_token_enc": base64.b64encode((refresh_token or "").encode()).decode(),
            "scopes": scopes or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        return self.store.append("tokens", token)

    def tokens(self) -> list[dict]:
        tokens = self.store.load("tokens", [])
        return [{k: v for k, v in t.items() if not k.endswith("_enc")} for t in tokens]
