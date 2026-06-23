from __future__ import annotations

from secondbrain.connectors.cursor_store import InMemoryCursorStore
from secondbrain.connectors.dead_letter import InMemoryDeadLetterQueue
from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem
from secondbrain.connectors.resilient_runner import ResilientIncrementalSyncRunner
from secondbrain.connectors.retry_policy import RetryPolicy
from secondbrain.connectors.sync_state import SyncStatus


class FlakyFetchConnector:
    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_since(self, cursor, limit):
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("temporary outage")
        return FetchBatch(items=[FetchedItem(id="1", payload={"x": 1}, cursor="c1")], next_cursor="c1")


class BrokenFetchConnector:
    name = "broken"

    def fetch_since(self, cursor, limit):
        raise RuntimeError("bad credentials")


class StaticConnector:
    name = "static"

    def fetch_since(self, cursor, limit):
        return FetchBatch(
            items=[
                FetchedItem(id="ok", payload="ok", cursor="1"),
                FetchedItem(id="bad", payload="bad", cursor="2"),
            ],
            next_cursor="2",
        )


def test_retry_policy_retries_retryable_exceptions_only():
    policy = RetryPolicy(max_attempts=2, base_delay_seconds=0.5)

    retryable = policy.classify(TimeoutError("x"), attempt=1)
    assert retryable.should_retry is True
    assert retryable.delay_seconds == 0.5

    exhausted = policy.classify(TimeoutError("x"), attempt=2)
    assert exhausted.should_retry is False
    assert exhausted.reason == "attempts_exhausted"

    non_retryable = policy.classify(ValueError("x"), attempt=1)
    assert non_retryable.should_retry is False
    assert non_retryable.reason == "non_retryable"


def test_fetch_retry_then_success_commits_cursor():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    connector = FlakyFetchConnector()
    runner = ResilientIncrementalSyncRunner(
        cursor_store,
        dlq,
        RetryPolicy(max_attempts=2, base_delay_seconds=0),
    )

    result = runner.run(connector, lambda item: True)

    assert result.status == SyncStatus.SUCCESS
    assert result.processed == 1
    assert result.cursor_after == "c1"
    assert cursor_store.get("flaky").value == "c1"
    assert dlq.list() == []
    assert len(runner.retry_traces) == 1
    assert runner.retry_traces[0].phase == "fetch"


def test_fatal_fetch_failure_does_not_commit_cursor_and_goes_to_dead_letter():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    runner = ResilientIncrementalSyncRunner(
        cursor_store,
        dlq,
        RetryPolicy(max_attempts=2, base_delay_seconds=0),
    )

    result = runner.run(BrokenFetchConnector(), lambda item: True)

    assert result.status == SyncStatus.FAILED
    assert result.cursor_after is None
    assert cursor_store.get("broken") is None
    letters = dlq.list("broken")
    assert len(letters) == 1
    assert letters[0].code == "fetch_error"
    assert letters[0].item_id is None


def test_item_failure_isolated_dead_lettered_and_cursor_committed():
    cursor_store = InMemoryCursorStore()
    dlq = InMemoryDeadLetterQueue()
    runner = ResilientIncrementalSyncRunner(
        cursor_store,
        dlq,
        RetryPolicy(max_attempts=1),
    )

    def handler(item):
        if item.id == "bad":
            raise ValueError("cannot parse")
        return True

    result = runner.run(StaticConnector(), handler)

    assert result.status == SyncStatus.PARTIAL
    assert result.processed == 1
    assert result.failed == 1
    assert result.cursor_after == "2"
    assert cursor_store.get("static").value == "2"
    letters = dlq.list("static")
    assert len(letters) == 1
    assert letters[0].item_id == "bad"
    assert letters[0].payload == "bad"


def test_dead_letter_queue_can_clear_per_connector():
    dlq = InMemoryDeadLetterQueue()
    from secondbrain.connectors.dead_letter import DeadLetter

    dlq.push(DeadLetter(connector="a", code="x", message="x"))
    dlq.push(DeadLetter(connector="b", code="x", message="x"))

    assert dlq.clear("a") == 1
    assert [letter.connector for letter in dlq.list()] == ["b"]
