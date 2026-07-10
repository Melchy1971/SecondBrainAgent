from __future__ import annotations

from typing import Any

from secondbrain.connectors.incremental_runner import FetchBatch
from secondbrain.connectors.scaffold.transport import FakeTransport, HttpResponse


class FakeConnectorProvider:
    def __init__(self, batches: list[FetchBatch | Exception] | None = None, *, name: str = "fake") -> None:
        self.name = name
        self.batches = list(batches or [])
        self.calls: list[tuple[str | None, int]] = []

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        self.calls.append((cursor, limit))
        if not self.batches:
            return FetchBatch(items=[], next_cursor=cursor, has_more=False)
        batch = self.batches.pop(0)
        if isinstance(batch, Exception):
            raise batch
        return batch


class FakeIncrementalConnector(FakeConnectorProvider):
    pass


class RecordingConnectorProvider(FakeConnectorProvider):
    pass


class ConnectorFakeTransport(FakeTransport):
    """Project-level alias for connector tests.

    The production transport fake lives in the connector scaffold. This alias
    keeps tests stable while making the dependency on a fake transport explicit.
    """

    def json_response(self, status: int, payload: Any, headers: dict[str, str] | None = None) -> HttpResponse:
        return super().json_response(status, payload, headers)


__all__ = [
    "ConnectorFakeTransport",
    "FakeConnectorProvider",
    "FakeIncrementalConnector",
    "RecordingConnectorProvider",
]
