from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .connector_job_models import ConnectorJob

SyncHandler = Callable[[str, str | None], dict[str, Any]]


class ConnectorJobRunner:
    def __init__(self, sync_handler: SyncHandler | None = None) -> None:
        self.sync_handler = sync_handler or self._default_sync_handler

    def run_sync(self, job: ConnectorJob) -> ConnectorJob:
        running = job.running()
        try:
            result = self.sync_handler(running.connector_id, running.cursor_before)
            return running.completed(
                items_processed=int(result.get("items_processed", 0)),
                cursor_after=result.get("cursor_after"),
            )
        except Exception as exc:  # deterministic UI-facing failure path
            return running.failed(str(exc))

    @staticmethod
    def _default_sync_handler(connector_id: str, cursor_before: str | None) -> dict[str, Any]:
        return {"items_processed": 0, "cursor_after": cursor_before}
