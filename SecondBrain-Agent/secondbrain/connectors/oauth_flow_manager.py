"""v30.4 - OAuth flow manager."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class OAuthClientConfig:
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    redirect_uri: str
    scopes: list[str]


class OAuthFlowManager:
    def __init__(self, config: OAuthClientConfig, http_client=None):
        self.config = config
        self.http_client = http_client

    def authorization_url(self, state: str) -> str:
        query = urlencode({
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        })
        return f"{self.config.auth_url}?{query}"

    def exchange_code(self, code: str) -> dict:
        if self.http_client is None:
            raise RuntimeError("http_client required for token exchange")
        return self.http_client.post_json(self.config.token_url, {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.config.redirect_uri,
        })
