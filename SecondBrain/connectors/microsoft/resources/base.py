"""M365 resource base classes built on the shared scaffold."""

from __future__ import annotations

from typing import Any

from secondbrain.connectors.scaffold.delta_connector import DeltaCollectionConnector, Normalizer, max_watermark
from secondbrain.connectors.scaffold.writer import ApprovalGatedWriter

# kept for backwards-compatible imports (e.g. teams.py)
_max_watermark = max_watermark


class GraphResourceConnector(DeltaCollectionConnector):
    def __init__(self, name: str, endpoint: str, normalizer: Normalizer, client, *,
                 delta: bool = True, prefer: str | None = None,
                 params: dict[str, Any] | None = None, watermark_field: str = "lastModifiedDateTime") -> None:
        super().__init__(
            name, endpoint, normalizer, client,
            delta_mode="path_suffix" if delta else "watermark",
            delta_suffix="/delta", prefer=prefer, params=params, watermark_field=watermark_field,
        )


class GraphWriter(ApprovalGatedWriter):
    resource = "graph"


__all__ = ["GraphResourceConnector", "GraphWriter", "_max_watermark"]
