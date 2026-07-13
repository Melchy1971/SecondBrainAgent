"""P1.2.5 - Connector adapter registry and lifecycle orchestration.

This module binds the P1.2 connector primitives into one executable adapter
lifecycle. It keeps adapter registration, normalized item processing, cursor
commit, dead-letter isolation, retry traces, and health reporting in one small
service without coupling the pipeline to vendor payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .adapter_contract import ConnectorAdapter, ConnectorContractError, ConnectorItem, validate_adapter
from .cursor_store import CursorStore, InMemoryCursorStore
from .dead_letter import DeadLetter, DeadLetterQueue, InMemoryDeadLetterQueue
from .health import ConnectorHealthReporter, ConnectorHealthSnapshot, InMemoryHealthSink
from .retry_policy import RetryPolicy
from .sync_state import SyncCursor, SyncIssue, SyncRunResult, SyncStatus
from .resilient_runner import RetryTrace, Sleeper

ItemProcessor = Callable[[ConnectorItem], bool]


@dataclass(frozen=True)
class RegisteredConnector:
    """Adapter metadata stored by the lifecycle registry."""

    source: str
    adapter: ConnectorAdapter
    enabled: bool = True
    labels: tuple[str, ...] = field(default_factory=tuple)


class ConnectorLifecycleRegistry:
    """In-memory registry for normalized connector adapters.

    Production deployments can replace this with a DB-backed registry behind the
    same method shape. The lifecycle service only depends on this tiny contract.
    """

    def __init__(self) -> None:
        self._items: dict[str, RegisteredConnector] = {}

    def register(
        self,
        adapter: ConnectorAdapter,
        *,
        enabled: bool = True,
        labels: Iterable[str] = (),
        replace: bool = False,
    ) -> RegisteredConnector:
        validated = validate_adapter(adapter)
        source = str(validated.source).strip().lower()
        if not replace and source in self._items:
            raise ConnectorContractError(f"connector already registered: {source}")
        record = RegisteredConnector(
            source=source,
            adapter=validated,
            enabled=bool(enabled),
            labels=tuple(str(label).strip() for label in labels if str(label).strip()),
        )
        self._items[source] = record
        return record

    def get(self, source: str) -> RegisteredConnector | None:
        return self._items.get(str(source).strip().lower())

    def require(self, source: str) -> RegisteredConnector:
        record = self.get(source)
        if record is None:
            raise KeyError(f"connector not registered: {source}")
        return record

    def enable(self, source: str) -> RegisteredConnector:
        current = self.require(source)
        updated = RegisteredConnector(source=current.source, adapter=current.adapter, enabled=True, labels=current.labels)
        self._items[current.source] = updated
        return updated

    def disable(self, source: str) -> RegisteredConnector:
        current = self.require(source)
        updated = RegisteredConnector(source=current.source, adapter=current.adapter, enabled=False, labels=current.labels)
        self._items[current.source] = updated
        return updated

    def list(self, *, enabled_only: bool = False) -> list[RegisteredConnector]:
        records = list(self._items.values())
        if enabled_only:
            records = [record for record in records if record.enabled]
        return sorted(records, key=lambda record: record.source)


@dataclass(frozen=True)
class ConnectorLifecycleRun:
    """Combined sync result and health snapshot for one connector run."""

    result: SyncRunResult
    health: ConnectorHealthSnapshot

    def to_dict(self) -> dict:
        return {"result": self.result.to_dict(), "health": self.health.to_dict()}


class ConnectorLifecycleService:
    """Run registered adapter syncs with cursor, resilience, and health reporting."""

    def __init__(
        self,
        registry: ConnectorLifecycleRegistry | None = None,
        cursor_store: CursorStore | None = None,
        dead_letters: DeadLetterQueue | None = None,
        retry_policy: RetryPolicy | None = None,
        health_reporter: ConnectorHealthReporter | None = None,
        *,
        sleeper: Sleeper | None = None,
    ) -> None:
        self.registry = registry or ConnectorLifecycleRegistry()
        self.cursor_store = cursor_store or InMemoryCursorStore()
        self.dead_letters = dead_letters or InMemoryDeadLetterQueue()
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_sink = InMemoryHealthSink()
        self.health_reporter = health_reporter or ConnectorHealthReporter(sink=self.health_sink)
        self.sleeper = sleeper or (lambda _seconds: None)
        self.retry_traces: list[RetryTrace] = []

    def register(self, adapter: ConnectorAdapter, **kwargs) -> RegisteredConnector:
        return self.registry.register(adapter, **kwargs)

    def run_one(self, source: str, processor: ItemProcessor) -> ConnectorLifecycleRun:
        record = self.registry.require(source)
        connector = record.source
        stored = self.cursor_store.get(connector)
        cursor_before = stored.value if stored else None
        result = SyncRunResult(
            connector=connector,
            status=SyncStatus.RUNNING,
            cursor_before=cursor_before,
            cursor_after=cursor_before,
        )

        if not record.enabled:
            result.skipped += 1
            finished = result.finish(SyncStatus.IDLE)
            return self._finish(connector, finished)

        try:
            items = self._fetch_with_retry(record.adapter, cursor_before)
        except Exception as exc:  # noqa: BLE001 - connector fetch failures must not advance cursors
            result.add_issue(SyncIssue(item_id=None, code="fetch_error", message=str(exc), fatal=True))
            self.dead_letters.push(
                DeadLetter(connector=connector, code="fetch_error", message=str(exc), cursor=cursor_before, attempts=self.retry_policy.max_attempts)
            )
            return self._finish(connector, result.finish(SyncStatus.FAILED))

        result.fetched = len(items)
        max_cursor = cursor_before
        for item in items:
            if item.source != connector:
                result.add_issue(
                    SyncIssue(
                        item_id=item.external_id,
                        code="source_mismatch",
                        message=f"item source {item.source!r} does not match connector {connector!r}",
                        fatal=False,
                    )
                )
                self.dead_letters.push(
                    DeadLetter(
                        connector=connector,
                        item_id=item.external_id,
                        code="source_mismatch",
                        message="Connector item source mismatch",
                        payload=_safe_item_payload(item),
                        cursor=cursor_before,
                    )
                )
                continue

            handled = self._process_with_retry(connector, item, processor, result)
            if handled is True:
                result.processed += 1
                max_cursor = _item_cursor(item)
            elif handled is False:
                result.skipped += 1

        result.cursor_after = max_cursor
        status = SyncStatus.SUCCESS if result.failed == 0 else SyncStatus.PARTIAL
        if result.cursor_after != cursor_before:
            self.cursor_store.save(SyncCursor(connector=connector, value=result.cursor_after))
        return self._finish(connector, result.finish(status))

    def run_enabled(self, processor: ItemProcessor) -> list[ConnectorLifecycleRun]:
        return [self.run_one(record.source, processor) for record in self.registry.list(enabled_only=True)]

    def _fetch_with_retry(self, adapter: ConnectorAdapter, cursor: str | None) -> list[ConnectorItem]:
        attempt = 1
        while True:
            try:
                items = adapter.fetch_changed(cursor)
                return [item if isinstance(item, ConnectorItem) else ConnectorItem(**item) for item in items]
            except Exception as exc:  # noqa: BLE001 - retry policy owns classification
                decision = self.retry_policy.classify(exc, attempt=attempt)
                self.retry_traces.append(
                    RetryTrace(phase="fetch", attempt=attempt, delay_seconds=decision.delay_seconds, reason=decision.reason, message=str(exc))
                )
                if not decision.should_retry:
                    raise
                self.sleeper(decision.delay_seconds)
                attempt += 1

    def _process_with_retry(
        self,
        connector: str,
        item: ConnectorItem,
        processor: ItemProcessor,
        result: SyncRunResult,
    ) -> bool | None:
        attempt = 1
        while True:
            try:
                return bool(processor(item))
            except Exception as exc:  # noqa: BLE001 - isolate item-level failures
                decision = self.retry_policy.classify(exc, attempt=attempt)
                self.retry_traces.append(
                    RetryTrace(phase="item", attempt=attempt, delay_seconds=decision.delay_seconds, reason=decision.reason, message=str(exc))
                )
                if decision.should_retry:
                    self.sleeper(decision.delay_seconds)
                    attempt += 1
                    continue
                result.add_issue(SyncIssue(item_id=item.external_id, code="handler_error", message=str(exc), fatal=False))
                self.dead_letters.push(
                    DeadLetter(
                        connector=connector,
                        item_id=item.external_id,
                        code="handler_error",
                        message=str(exc),
                        payload=_safe_item_payload(item),
                        cursor=_item_cursor(item),
                        attempts=attempt,
                    )
                )
                return None

    def _finish(self, connector: str, result: SyncRunResult) -> ConnectorLifecycleRun:
        health = self.health_reporter.report(
            connector=connector,
            result=result,
            cursor_store=self.cursor_store,
            dead_letters=self.dead_letters,
            retry_traces=self.retry_traces,
        )
        return ConnectorLifecycleRun(result=result, health=health)


def _item_cursor(item: ConnectorItem) -> str:
    return item.updated_at.isoformat()


def _safe_item_payload(item: ConnectorItem) -> dict:
    return {
        "external_id": item.external_id,
        "source": item.source,
        "title": item.title,
        "uri": item.uri,
        "mime_type": item.mime_type,
        "updated_at": item.updated_at.isoformat(),
        "content_hash": item.content_hash,
    }
