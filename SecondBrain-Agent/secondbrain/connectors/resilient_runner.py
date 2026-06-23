"""P1.2.2 - Resilient connector sync runner.

Adds bounded retry handling and a dead-letter queue on top of the P1.2.1
incremental sync contract. Cursor commits remain conservative: fatal fetch
errors do not advance the cursor, while item-level failures are isolated and
stored as dead letters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .cursor_store import CursorStore, InMemoryCursorStore
from .dead_letter import DeadLetter, DeadLetterQueue, InMemoryDeadLetterQueue
from .incremental_runner import FetchBatch, FetchedItem, IncrementalConnector, ItemHandler
from .retry_policy import RetryPolicy
from .sync_state import SyncCursor, SyncIssue, SyncRunResult, SyncStatus

Sleeper = Callable[[float], None]


@dataclass(frozen=True)
class RetryTrace:
    phase: str
    attempt: int
    delay_seconds: float
    reason: str
    message: str


class ResilientIncrementalSyncRunner:
    def __init__(
        self,
        cursor_store: CursorStore | None = None,
        dead_letters: DeadLetterQueue | None = None,
        retry_policy: RetryPolicy | None = None,
        *,
        batch_size: int = 100,
        max_batches: int = 100,
        sleeper: Sleeper | None = None,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if max_batches <= 0:
            raise ValueError("max_batches must be > 0")
        self.cursor_store = cursor_store or InMemoryCursorStore()
        self.dead_letters = dead_letters or InMemoryDeadLetterQueue()
        self.retry_policy = retry_policy or RetryPolicy()
        self.batch_size = batch_size
        self.max_batches = max_batches
        self.sleeper = sleeper or (lambda _seconds: None)
        self.retry_traces: list[RetryTrace] = []

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
                batch = self._fetch_with_retry(connector, active_cursor)
                result.fetched += len(batch.items)
                active_cursor = self._resolve_cursor(active_cursor, batch)

                for item in batch.items:
                    self._handle_item(connector_name, item, handler, result)

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
        except Exception as exc:  # noqa: BLE001 - fatal fetch failure; cursor must not advance
            result.add_issue(SyncIssue(item_id=None, code="fetch_error", message=str(exc), fatal=True))
            self.dead_letters.push(
                DeadLetter(
                    connector=connector_name,
                    item_id=None,
                    cursor=active_cursor,
                    code="fetch_error",
                    message=str(exc),
                    attempts=self.retry_policy.max_attempts,
                )
            )
            result.cursor_after = cursor_before
            return result.finish(SyncStatus.FAILED)

        status = SyncStatus.SUCCESS if result.failed == 0 else SyncStatus.PARTIAL
        if result.cursor_after != cursor_before:
            self.cursor_store.save(SyncCursor(connector=connector_name, value=result.cursor_after))
        return result.finish(status)

    def _fetch_with_retry(self, connector: IncrementalConnector, cursor: str | None) -> FetchBatch:
        attempt = 1
        while True:
            try:
                return connector.fetch_since(cursor, self.batch_size)
            except Exception as exc:  # noqa: BLE001 - policy decides retryability
                decision = self.retry_policy.classify(exc, attempt=attempt)
                self.retry_traces.append(
                    RetryTrace(
                        phase="fetch",
                        attempt=attempt,
                        delay_seconds=decision.delay_seconds,
                        reason=decision.reason,
                        message=str(exc),
                    )
                )
                if not decision.should_retry:
                    raise
                self.sleeper(decision.delay_seconds)
                attempt += 1

    def _handle_item(
        self,
        connector_name: str,
        item: FetchedItem,
        handler: ItemHandler,
        result: SyncRunResult,
    ) -> None:
        attempt = 1
        while True:
            try:
                handled = bool(handler(item))
                if handled:
                    result.processed += 1
                else:
                    result.skipped += 1
                return
            except Exception as exc:  # noqa: BLE001 - item failure isolation
                decision = self.retry_policy.classify(exc, attempt=attempt)
                self.retry_traces.append(
                    RetryTrace(
                        phase="item",
                        attempt=attempt,
                        delay_seconds=decision.delay_seconds,
                        reason=decision.reason,
                        message=str(exc),
                    )
                )
                if decision.should_retry:
                    self.sleeper(decision.delay_seconds)
                    attempt += 1
                    continue

                result.add_issue(SyncIssue(item_id=item.id, code="handler_error", message=str(exc)))
                self.dead_letters.push(
                    DeadLetter(
                        connector=connector_name,
                        item_id=item.id,
                        payload=item.payload,
                        cursor=item.cursor,
                        code="handler_error",
                        message=str(exc),
                        attempts=attempt,
                    )
                )
                return

    @staticmethod
    def _resolve_cursor(current: str | None, batch: FetchBatch) -> str | None:
        if batch.next_cursor is not None:
            return batch.next_cursor
        for item in reversed(batch.items):
            if item.cursor is not None:
                return item.cursor
        return current
