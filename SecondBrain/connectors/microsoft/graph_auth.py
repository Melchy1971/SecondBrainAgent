"""M365 authenticator: OAuth2 device-code flow via the shared scaffold."""

from __future__ import annotations

import time
from typing import Callable

from secondbrain.connectors.token_repository import TokenRepository
from secondbrain.connectors.token_refresh import TokenRefreshService
from secondbrain.connectors.scaffold.oauth2 import (
    OAuth2Authenticator, OAuth2Config, DeviceCodeStart, OAuth2Error,
)
from secondbrain.connectors.microsoft.config import GraphConfig
from secondbrain.connectors.scaffold.transport import Transport

PROVIDER = "m365"
GraphAuthError = OAuth2Error  # backwards-compatible alias


class GraphAuthenticator(OAuth2Authenticator):
    def __init__(self, config: GraphConfig, *, transport: Transport | None = None,
                 token_repo: TokenRepository | None = None,
                 refresh_service: TokenRefreshService | None = None,
                 clock: Callable[[], float] = time.time, provider: str = PROVIDER) -> None:
        oauth = OAuth2Config(
            client_id=config.client_id,
            scopes=tuple(config.scopes),
            token_url=config.token_url,
            devicecode_url=config.devicecode_url,
            provider=provider,
            token_store_path=config.token_store_path,
        )
        super().__init__(oauth, transport=transport,
                         token_repo=token_repo or TokenRepository(config.token_store_path),
                         refresh_service=refresh_service, clock=clock)
        self.graph_config = config


__all__ = ["GraphAuthenticator", "GraphAuthError", "DeviceCodeStart", "OAuth2Error", "PROVIDER"]
