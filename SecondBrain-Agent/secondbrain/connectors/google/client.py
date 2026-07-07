"""Google REST client: shared RestClient with Google paging + per-API paging presets."""

from __future__ import annotations

import time
from typing import Callable

from secondbrain.connectors.retry_backoff import ConnectorRetryBackoff
from secondbrain.connectors.scaffold.rest_client import RestClient, RestApiError, PagingConfig, GOOGLE_PAGING
from secondbrain.connectors.scaffold.transport import Transport
from secondbrain.connectors.google.config import GoogleConfig
from secondbrain.connectors.google.auth import GoogleAuthenticator

# per-API paging variants (Google field names differ per endpoint)
CONTACTS_PAGING = PagingConfig(items_key="connections", next_key="nextPageToken",
                               delta_key="nextSyncToken", next_is_url=False, next_param="pageToken", top_param="pageSize")
GMAIL_LIST_PAGING = PagingConfig(items_key="messages", next_key="nextPageToken",
                                 delta_key="_none_", next_is_url=False, next_param="pageToken", top_param="maxResults")
DRIVE_CHANGES_PAGING = PagingConfig(items_key="changes", next_key="nextPageToken",
                                    delta_key="newStartPageToken", next_is_url=False, next_param="pageToken", top_param="pageSize")

GoogleApiError = RestApiError


class GoogleClient(RestClient):
    def __init__(self, config: GoogleConfig, auth: GoogleAuthenticator, *,
                 transport: Transport | None = None, retry: ConnectorRetryBackoff | None = None,
                 sleeper: Callable[[float], None] = time.sleep, max_retries: int = 5) -> None:
        super().__init__(config.api_base_url, auth, transport=transport, paging=GOOGLE_PAGING,
                         retry=retry, sleeper=sleeper, max_retries=max_retries)
        self.config = config


__all__ = ["GoogleClient", "GoogleApiError", "CONTACTS_PAGING", "GMAIL_LIST_PAGING", "DRIVE_CHANGES_PAGING"]
