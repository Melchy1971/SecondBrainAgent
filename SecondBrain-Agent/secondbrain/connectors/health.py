"""P1.2.3 - Connector health and observability primitives.

Turns raw sync results, retry traces, cursor state, and dead letters into a
stable health snapshot. The module is deliberately storage-neutral so it can be
used by CLI, GUI, release gates, and future API endpoints without pulling in a
web framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from .cursor_store import CursorStore
from .dead_letter import DeadLetterQueue
from .resilient_runner import RetryTrace
from .sync_state import SyncRunResult, SyncStatus


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConnectorHealthPolicy:
    max_dead_letters: int = 0
    max_retry_traces: int = 0
    partial_is_degraded: bool = True

    def __post_init__(self) -> None:
        if self.max_dead_letters < 0:
            raise ValueError("max_dead_letters must be >= 0")
        if self.max_retry_traces < 0:
            raise ValueError("max_retry_traces must be >= 0")


@dataclass(frozen=True)
class ConnectorHealthSnapshot:
    connector: str
    status: HealthStatus
    last_sync_status: str | None = None
    cursor: str | None = None
    fetched: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0
    dead_letters: int = 0
    retry_traces: int = 0
    issues: list[dict[str, Any]] = field(default_factory=list)
    checked_at: str = field(default_factory=utc_now_iso)

    @property
    def ok(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "connector": self.connector,
            "status": self.status.value,
            "ok": self.ok,
            "last_sync_status": self.last_sync_status,
            "cursor": self.cursor,
            "fetched": self.fetched,
            "processed": self.processed,
            "skipped": self.skipped,
            "failed": self.failed,
            "dead_letters": self.dead_letters,
            "retry_traces": self.retry_traces,
            "issues": list(self.issues),
            "checked_at": self.checked_at,
        }


class HealthSink(Protocol):
    def record(self, snapshot: ConnectorHealthSnapshot) -> None: ...


class InMemoryHealthSink:
    def __init__(self) -> None:
        self._snapshots: list[ConnectorHealthSnapshot] = []

    def record(self, snapshot: ConnectorHealthSnapshot) -> None:
        self._snapshots.append(snapshot)

    def latest(self, connector: str | None = None) -> ConnectorHealthSnapshot | None:
        snapshots = self._snapshots
        if connector is not None:
            snapshots = [snapshot for snapshot in snapshots if snapshot.connector == connector]
        return snapshots[-1] if snapshots else None

    def list(self, connector: str | None = None) -> list[ConnectorHealthSnapshot]:
        if connector is None:
            return list(self._snapshots)
        return [snapshot for snapshot in self._snapshots if snapshot.connector == connector]


class ConnectorHealthEvaluator:
    def __init__(self, policy: ConnectorHealthPolicy | None = None) -> None:
        self.policy = policy or ConnectorHealthPolicy()

    def evaluate(
        self,
        *,
        connector: str,
        result: SyncRunResult | None = None,
        cursor_store: CursorStore | None = None,
        dead_letters: DeadLetterQueue | None = None,
        retry_traces: list[RetryTrace] | None = None,
    ) -> ConnectorHealthSnapshot:
        cursor = None
        if cursor_store is not None:
            stored = cursor_store.get(connector)
            cursor = stored.value if stored else None

        dead_letter_count = len(dead_letters.list(connector)) if dead_letters is not None else 0
        retry_count = len(retry_traces or [])
        issues: list[dict[str, Any]] = []

        if result is None:
            status = HealthStatus.UNKNOWN
            last_sync_status = None
            fetched = processed = skipped = failed = 0
        else:
            last_sync_status = result.status.value
            fetched = result.fetched
            processed = result.processed
            skipped = result.skipped
            failed = result.failed
            issues.extend(issue.to_dict() for issue in result.issues)
            status = self._status_from_result(result)

        if dead_letter_count > self.policy.max_dead_letters:
            issues.append(
                {
                    "item_id": None,
                    "code": "dead_letter_threshold_exceeded",
                    "message": f"{dead_letter_count} dead letters exceed threshold {self.policy.max_dead_letters}",
                    "fatal": False,
                }
            )
            status = self._worse(status, HealthStatus.DEGRADED)

        if retry_count > self.policy.max_retry_traces:
            issues.append(
                {
                    "item_id": None,
                    "code": "retry_threshold_exceeded",
                    "message": f"{retry_count} retry traces exceed threshold {self.policy.max_retry_traces}",
                    "fatal": False,
                }
            )
            status = self._worse(status, HealthStatus.DEGRADED)

        return ConnectorHealthSnapshot(
            connector=connector,
            status=status,
            last_sync_status=last_sync_status,
            cursor=cursor,
            fetched=fetched,
            processed=processed,
            skipped=skipped,
            failed=failed,
            dead_letters=dead_letter_count,
            retry_traces=retry_count,
            issues=issues,
        )

    def _status_from_result(self, result: SyncRunResult) -> HealthStatus:
        if result.status == SyncStatus.SUCCESS:
            return HealthStatus.HEALTHY
        if result.status == SyncStatus.PARTIAL:
            return HealthStatus.DEGRADED if self.policy.partial_is_degraded else HealthStatus.HEALTHY
        if result.status == SyncStatus.FAILED:
            return HealthStatus.FAILED
        if result.status == SyncStatus.RUNNING:
            return HealthStatus.DEGRADED
        return HealthStatus.UNKNOWN

    @staticmethod
    def _worse(current: HealthStatus, candidate: HealthStatus) -> HealthStatus:
        order = {
            HealthStatus.UNKNOWN: 0,
            HealthStatus.HEALTHY: 1,
            HealthStatus.DEGRADED: 2,
            HealthStatus.FAILED: 3,
        }
        return candidate if order[candidate] > order[current] else current


class ConnectorHealthReporter:
    def __init__(self, evaluator: ConnectorHealthEvaluator | None = None, sink: HealthSink | None = None) -> None:
        self.evaluator = evaluator or ConnectorHealthEvaluator()
        self.sink = sink

    def report(self, **kwargs: Any) -> ConnectorHealthSnapshot:
        snapshot = self.evaluator.evaluate(**kwargs)
        if self.sink is not None:
            self.sink.record(snapshot)
        return snapshot
