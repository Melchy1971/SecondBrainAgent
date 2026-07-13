"""Provider-agnostic background sync: delta fetch -> import bridge -> ingestion sink."""

from __future__ import annotations

import time
from typing import Any, Callable

from secondbrain.connectors.cursor_store import CursorStore, InMemoryCursorStore
from secondbrain.connectors.incremental_runner import IncrementalSyncRunner
from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.connectors.sync_audit import SyncAudit


class BackgroundSync:
    def __init__(self, connectors: dict[str, Any], *, sink: ImportJobSink | None = None,
                 cursor_store: CursorStore | None = None, audit: SyncAudit | None = None,
                 batch_size: int = 100) -> None:
        self.connectors = connectors
        self.sink = sink or InMemoryImportJobSink()
        self.cursor_store = cursor_store or InMemoryCursorStore()
        self.audit = audit or SyncAudit()
        self.batch_size = batch_size

    def run_once(self, resources=None) -> dict[str, dict]:
        names = resources or list(self.connectors.keys())
        runner = IncrementalSyncRunner(self.cursor_store, batch_size=self.batch_size)
        results: dict[str, dict] = {}
        for name in names:
            connector = self.connectors.get(name)
            if connector is None:
                continue
            bridge = ConnectorImportBridge(sink=self.sink)
            handler = lambda item, _b=bridge: _b.process_item(item.payload)
            result = runner.run(connector, handler)
            self.audit.record(connector.name, result.status.value, result.processed)
            summary = result.to_dict()
            summary["import"] = bridge.snapshot()
            results[name] = summary
        return results

    def run_forever(self, interval_seconds: float, *, stop: Callable[[], bool],
                    sleeper: Callable[[float], None] = time.sleep, max_cycles: int | None = None) -> int:
        cycles = 0
        while not stop():
            self.run_once()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            sleeper(interval_seconds)
        return cycles
