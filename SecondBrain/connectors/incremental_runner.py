"""P1.2.1 - Connector incremental sync runner.

The runner separates external fetching from internal processing. Cursor commits
happen only when the run is successful or partial. Fatal fetch errors keep the
old cursor to prevent silent data gaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol

from .cursor_store import CursorStore, InMemoryCursorStore
from .sync_state import SyncCursor, SyncIssue, SyncRunResult, SyncStatus


@dataclass(frozen=True)
class FetchedItem:
    id: str
    payload: Any
    cursor: str | None = None


@dataclass(frozen=True)
class FetchBatch:
    items: list[FetchedItem]
    next_cursor: str | None = None
    has_more: bool = False


class IncrementalConnector(Protocol):
    name: str
    def fetch_since(self, cursor: str | None, limit: int) -> FetchBatch: ...


ItemHandler = Callable[[FetchedItem], bool]


class IncrementalSyncRunner:
    def __init__(
        self,
        cursor_store: CursorStore | None = None,
        *,
        batch_size: int = 100,
        max_batches: int = 100,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if max_batches <= 0:
            raise ValueError("max_batches must be > 0")
        self.cursor_store = cursor_store or InMemoryCursorStore()
        self.batch_size = batch_size
        self.max_batches = max_batches

    def run(self, connector: IncrementalConnector, handler: ItemHandler) -> SyncRunResult:
        connector_name = str(connector.name)
        stored = self.cursor_store.get(connector_name)
        cursor_before = stored.value if stored else None
        active_cursor = cursor_before
        result = SyncRunResult(
            connector=connector_name,
            status=SyncStatus.RUNNING,
            cursor_before=cursor_before,
            cursor_after=cursor_before,
        )

        try:
            for _ in range(self.max_batches):
                batch = connector.fetch_since(active_cursor, self.batch_size)
                result.fetched += len(batch.items)
                active_cursor = self._resolve_cursor(active_cursor, batch)

                for item in batch.items:
                    try:
                        handled = bool(handler(item))
                    except Exception as exc:  # noqa: BLE001 - isolate item failure by design
                        result.add_issue(SyncIssue(item_id=item.id, code="handler_error", message=str(exc)))
                        continue

                    if handled:
                        result.processed += 1
                    else:
                        result.skipped += 1

                result.cursor_after = active_cursor
                if not batch.has_more:
                    break
            else:
                result.add_issue(
                    SyncIssue(
                        item_id=None,
                        code="max_batches_reached",
                        message="Sync stopped before connector reported completion",
                        fatal=False,
                    )
                )

        except Exception as exc:  # noqa: BLE001 - fatal connector failures must not commit cursor
            result.add_issue(SyncIssue(item_id=None, code="fetch_error", message=str(exc), fatal=True))
            result.cursor_after = cursor_before
            return result.finish(SyncStatus.FAILED)

        status = SyncStatus.SUCCESS if result.failed == 0 else SyncStatus.PARTIAL
        if result.cursor_after != cursor_before:
            self.cursor_store.save(SyncCursor(connector=connector_name, value=result.cursor_after))
        return result.finish(status)

    @staticmethod
    def _resolve_cursor(current: str | None, batch: FetchBatch) -> str | None:
        if batch.next_cursor is not None:
            return batch.next_cursor
        for item in reversed(batch.items):
            if item.cursor is not None:
                return item.cursor
        return current


def items_from_payloads(payloads: Iterable[Any], *, start_index: int = 0) -> list[FetchedItem]:
    return [FetchedItem(id=str(index), payload=payload, cursor=str(index)) for index, payload in enumerate(payloads, start_index)]
