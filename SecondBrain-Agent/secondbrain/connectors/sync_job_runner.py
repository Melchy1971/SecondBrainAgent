"""v30.4 - connector sync job runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time

from secondbrain.connectors.sync_models import SyncResult


@dataclass(frozen=True)
class SyncJobReport:
    status: str
    results: list[SyncResult]
    started_at: float = field(default_factory=time)


class SyncJobRunner:
    def run(self, services: list, cursors: dict[str, str | None] | None = None) -> SyncJobReport:
        cursors = cursors or {}
        results = []
        errors = []
        for service in services:
            try:
                results.append(service.sync(cursor=cursors.get(service.connector)))
            except Exception as exc:
                errors.append(SyncResult(
                    connector=getattr(service, "connector", "unknown"),
                    status="FAIL",
                    items=0,
                    errors=[str(exc)],
                ))
        all_results = results + errors
        status = "PASS" if not errors else "FAIL"
        return SyncJobReport(status=status, results=all_results)
