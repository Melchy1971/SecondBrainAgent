"""Google authenticator: OAuth2 device-code flow via the shared scaffold."""

from __future__ import annotations

import time
from typing import Callable

from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.token_refresh import TokenRefreshService
from secondbrain.connectors.scaffold.oauth2 import OAuth2Authenticator, OAuth2Config, OAuth2Error
from secondbrain.connectors.scaffold.transport import Transport
from secondbrain.connectors.google.config import GoogleConfig

PROVIDER = "google"
GoogleAuthError = OAuth2Error


class GoogleAuthenticator(OAuth2Authenticator):
    def __init__(self, config: GoogleConfig, *, transport: Transport | None = None,
                 token_repo: TokenRepository | None = None,
                 refresh_service: TokenRefreshService | None = None,
                 clock: Callable[[], float] = time.time, provider: str = PROVIDER) -> None:
        oauth = OAuth2Config(
            client_id=config.client_id,
            client_secret=config.client_secret,   # Google requires it even for installed apps
            scopes=tuple(config.scopes),
            token_url=config.token_url,
            devicecode_url=config.devicecode_url,
            provider=provider,
            token_store_path=config.token_store_path,
        )
        super().__init__(oauth, transport=transport,
                         token_repo=token_repo or TokenRepository(config.token_store_path),
                         refresh_service=refresh_service, clock=clock)
        self.google_config = config


__all__ = ["GoogleAuthenticator", "GoogleAuthError", "PROVIDER"]
