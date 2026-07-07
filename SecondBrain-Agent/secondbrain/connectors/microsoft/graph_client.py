"""M365 Graph client: shared RestClient + Graph-specific JSON $batch."""

from __future__ import annotations

import time
from typing import Any, Callable, Iterable

from secondbrain.connectors.retry_backoff import ConnectorRetryBackoff
from secondbrain.connectors.scaffold.rest_client import RestClient, RestApiError, GRAPH_PAGING
from secondbrain.connectors.scaffold.transport import Transport
from secondbrain.connectors.microsoft.config import GraphConfig
from secondbrain.connectors.microsoft.graph_auth import GraphAuthenticator

BATCH_MAX = 20
GraphApiError = RestApiError  # backwards-compatible alias


class GraphClient(RestClient):
    def __init__(self, config: GraphConfig, auth: GraphAuthenticator, *,
                 transport: Transport | None = None, retry: ConnectorRetryBackoff | None = None,
                 sleeper: Callable[[float], None] = time.sleep, max_retries: int = 5) -> None:
        super().__init__(config.graph_base_url, auth, transport=transport, paging=GRAPH_PAGING,
                         retry=retry, sleeper=sleeper, max_retries=max_retries)
        self.config = config

    def batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        responses: list[dict[str, Any]] = []
        for chunk in _chunks(requests, BATCH_MAX):
            payload = {"requests": [self._norm_batch_req(i, r) for i, r in enumerate(chunk, start=1)]}
            resp = self.post("$batch", payload)
            responses.extend(resp.json().get("responses", []))
        return responses

    @staticmethod
    def _norm_batch_req(idx: int, req: dict[str, Any]) -> dict[str, Any]:
        out = {"id": str(req.get("id", idx)), "method": req.get("method", "GET").upper(), "url": req["url"]}
        if "body" in req and req["body"] is not None:
            out["body"] = req["body"]
            out["headers"] = {"Content-Type": "application/json", **(req.get("headers") or {})}
        elif req.get("headers"):
            out["headers"] = req["headers"]
        return out


def _chunks(seq: list, size: int) -> Iterable[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


__all__ = ["GraphClient", "GraphApiError", "BATCH_MAX"]
