"""Generic IncrementalConnector over a REST collection (delta or watermark)."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.adapter_contract import ConnectorItem

Normalizer = Callable[[Mapping[str, Any]], ConnectorItem | None]


class DeltaCollectionConnector:
    """delta_mode:
    - 'path_suffix'      : GET <endpoint><delta_suffix>; cursor = delta link (Graph)
    - 'sync_token_param' : GET <endpoint>?<sync_param>=<cursor>; cursor = delta token (Google)
    - 'watermark'        : order by watermark_field, filter gt cursor
    """

    def __init__(
        self,
        name: str,
        endpoint: str,
        normalizer: Normalizer,
        client,
        *,
        delta_mode: str = "path_suffix",
        delta_suffix: str = "/delta",
        sync_param: str = "syncToken",
        prefer: str | None = None,
        params: dict[str, Any] | None = None,
        watermark_field: str = "lastModifiedDateTime",
        paging=None,
    ) -> None:
        self.name = name
        self.endpoint = endpoint
        self.normalizer = normalizer
        self.client = client
        self.delta_mode = delta_mode
        self.delta_suffix = delta_suffix
        self.sync_param = sync_param
        self.prefer = prefer
        self.params = params or {}
        self.watermark_field = watermark_field
        self.paging = paging

    def _pg(self):
        return self.paging or self.client.paging

    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch:
        if self.delta_mode == "path_suffix":
            start = cursor or f"{self.endpoint}{self.delta_suffix}"
            params = None if cursor else {**self.params, self._pg().top_param: limit}
            raw, delta = self.client.follow_collection(start, params=params, delta=True, prefer=self.prefer, paging=self.paging)
            return FetchBatch(self._items(raw, delta), next_cursor=delta or cursor, has_more=False)

        if self.delta_mode == "sync_token_param":
            params = {**self.params, self._pg().top_param: limit}
            if cursor:
                params[self.sync_param] = cursor
            raw, delta = self.client.follow_collection(self.endpoint, params=params, delta=True, prefer=self.prefer, paging=self.paging)
            return FetchBatch(self._items(raw, delta), next_cursor=delta or cursor, has_more=False)

        # watermark
        params = {**self.params, self._pg().top_param: limit,
                  "$orderby": f"{self.watermark_field} desc"}
        if cursor:
            params["$filter"] = f"{self.watermark_field} gt {cursor}"
        raw, _ = self.client.follow_collection(self.endpoint, params=params, delta=False, paging=self.paging)
        watermark = max_watermark(raw, self.watermark_field, cursor)
        return FetchBatch(self._items(raw, watermark), next_cursor=watermark, has_more=False)

    def _items(self, raw: list[dict], cursor: str | None) -> list[FetchedItem]:
        out: list[FetchedItem] = []
        for payload in raw:
            ci = self.normalizer(payload)
            if ci is None:
                continue
            out.append(FetchedItem(id=ci.external_id, payload=ci, cursor=cursor))
        return out


def max_watermark(raw: list[dict], field: str, current: str | None) -> str | None:
    values = [str(p.get(field)) for p in raw if p.get(field)]
    if not values:
        return current
    newest = max(values)
    return current if (current and current >= newest) else newest
