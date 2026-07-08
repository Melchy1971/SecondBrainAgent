"""GitHub auth: static PAT provider or device-flow OAuth via the scaffold."""

from __future__ import annotations

import time
from typing import Callable

from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.scaffold.oauth2 import OAuth2Authenticator, OAuth2Config
from secondbrain.connectors.scaffold.transport import Transport
from secondbrain.connectors.github.config import GitHubConfig, DEVICE_URL, TOKEN_URL


class PatTokenProvider:
    """Personal access token provider (no refresh)."""

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("empty GitHub token")
        self._token = token

    def access_token(self) -> str:
        return self._token


class GitHubDeviceAuth(OAuth2Authenticator):
    def __init__(self, config: GitHubConfig, *, transport: Transport | None = None,
                 token_repo: TokenRepository | None = None, clock: Callable[[], float] = time.time) -> None:
        oauth = OAuth2Config(client_id=config.client_id, scopes=tuple(config.scopes),
                             token_url=TOKEN_URL, devicecode_url=DEVICE_URL, provider="github",
                             token_store_path=config.token_store_path, device_scope_separator=" ")
        super().__init__(oauth, transport=transport,
                         token_repo=token_repo or TokenRepository(config.token_store_path), clock=clock)


def token_provider_from_config(config: GitHubConfig, *, transport=None):
    if config.token:
        return PatTokenProvider(config.token)
    return GitHubDeviceAuth(config, transport=transport)
