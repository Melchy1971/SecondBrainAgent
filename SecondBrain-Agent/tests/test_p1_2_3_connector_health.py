from __future__ import annotations

from secondbrain.connectors.cursor_store import InMemoryCursorStore
from secondbrain.connectors.dead_letter import DeadLetter, InMemoryDeadLetterQueue
from secondbrain.connectors.health import (
    ConnectorHealthEvaluator,
    ConnectorHealthPolicy,
    ConnectorHealthReporter,
    HealthStatus,
    InMemoryHealthSink,
)
from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.resilient_runner import ResilientIncrementalSyncRunner
from secondbrain.connectors.retry_policy import RetryPolicy
from secondbrain.connectors.sync_state import SyncStatus


class StaticConnector:
    name = "static-health"

    def fetch_since(self, cursor, limit):
        return FetchBatch(items=[FetchedItem(id="1", payload={"x": 1}, cursor="c1")], next_cursor="c1")


class PartialConnector:
    name = "partial-health"

    def fetch_since(self, cursor, limit):
        return FetchBatch(
            items=[
                FetchedItem(id="ok", payload="ok", cursor="1"),
                FetchedItem(id="bad", payload="bad", cursor="2"),
            ],
            next_cursor="2",
        )


class BrokenConnector:
    name = "broken-health"

    def fetch_since(self, cursor, limit):
        raise RuntimeError("remote unavailable")


def test_successful_connector_health_is_healthy_and_serializable():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    runner = ResilientIncrementalSyncRunner(cursor_store, dlq)
    result = runner.run(StaticConnector(), lambda item: True)

    snapshot = ConnectorHealthEvaluator().evaluate(
        connector="static-health",
        result=result,
        cursor_store=cursor_store,
        dead_letters=dlq,
        retry_traces=runner.retry_traces,
    )

    data = snapshot.to_dict()
    assert snapshot.status == HealthStatus.HEALTHY
    assert snapshot.ok is True
    assert data["cursor"] == "c1"
    assert data["processed"] == 1
    assert data["dead_letters"] == 0
    assert data["last_sync_status"] == SyncStatus.SUCCESS.value


def test_partial_sync_with_dead_letter_is_degraded():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    runner = ResilientIncrementalSyncRunner(cursor_store, dlq, RetryPolicy(max_attempts=1))

    def handler(item):
        if item.id == "bad":
            raise ValueError("cannot parse")
        return True

    result = runner.run(PartialConnector(), handler)
    snapshot = ConnectorHealthEvaluator().evaluate(
        connector="partial-health",
        result=result,
        cursor_store=cursor_store,
        dead_letters=dlq,
        retry_traces=runner.retry_traces,
    )

    assert snapshot.status == HealthStatus.DEGRADED
    assert snapshot.failed == 1
    assert snapshot.dead_letters == 1
    assert any(issue["code"] == "handler_error" for issue in snapshot.issues)


def test_failed_fetch_is_failed_and_cursor_not_reported_as_advanced():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    runner = ResilientIncrementalSyncRunner(cursor_store, dlq, RetryPolicy(max_attempts=1))
    result = runner.run(BrokenConnector(), lambda item: True)

    snapshot = ConnectorHealthEvaluator().evaluate(
        connector="broken-health",
        result=result,
        cursor_store=cursor_store,
        dead_letters=dlq,
        retry_traces=runner.retry_traces,
    )

    assert snapshot.status == HealthStatus.FAILED
    assert snapshot.cursor is None
    assert snapshot.dead_letters == 1
    assert any(issue["fatal"] is True for issue in snapshot.issues)


def test_thresholds_degrade_even_without_current_sync_result():
    dlq = InMemoryDeadLetterQueue()
    dlq.push(DeadLetter(connector="gmail", code="parse_error", message="bad payload"))

    snapshot = ConnectorHealthEvaluator(ConnectorHealthPolicy(max_dead_letters=0)).evaluate(
        connector="gmail",
        dead_letters=dlq,
    )

    assert snapshot.status == HealthStatus.DEGRADED
    assert snapshot.last_sync_status is None
    assert snapshot.dead_letters == 1
    assert any(issue["code"] == "dead_letter_threshold_exceeded" for issue in snapshot.issues)


def test_reporter_records_snapshots_in_sink():
    sink = InMemoryHealthSink()
    reporter = ConnectorHealthReporter(sink=sink)

    snapshot = reporter.report(connector="drive")

    assert snapshot.status == HealthStatus.UNKNOWN
    assert sink.latest("drive") == snapshot
    assert sink.list("drive") == [snapshot]
