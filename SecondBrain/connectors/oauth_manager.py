"""P4 v22.0 - OAuth Framework Foundation."""

from dataclasses import dataclass
from time import time


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str | None = None
    expires_at: float = 0.0


class OAuthManager:
    def __init__(self):
        self._tokens: dict[str, OAuthToken] = {}

    def store(self, provider: str, token: OAuthToken):
        self._tokens[provider] = token

    def get(self, provider: str):
        return self._tokens.get(provider)

    def is_expired(self, provider: str) -> bool:
        token = self._tokens.get(provider)
        return True if token is None else token.expires_at <= time()
