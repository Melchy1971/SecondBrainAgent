from __future__ import annotations

from pathlib import Path

from secondbrain.connectors.cursor_store import InMemoryCursorStore, JsonCursorStore
from secondbrain.connectors.incremental_runner import FetchBatch, FetchedItem, IncrementalSyncRunner
from secondbrain.connectors.sync_state import SyncCursor, SyncStatus


class FakeConnector:
    name = "fake"

    def __init__(self, batches):
        self.batches = list(batches)
        self.calls = []

    def fetch_since(self, cursor, limit):
        self.calls.append((cursor, limit))
        if not self.batches:
            return FetchBatch(items=[], next_cursor=cursor, has_more=False)
        batch = self.batches.pop(0)
        if isinstance(batch, Exception):
            raise batch
        return batch


def test_runner_commits_cursor_after_successful_sync():
    store = InMemoryCursorStore()
    connector = FakeConnector([
        FetchBatch(items=[FetchedItem("a", {"x": 1}, cursor="c1")], next_cursor="c1"),
    ])
    handled = []

    result = IncrementalSyncRunner(store, batch_size=10).run(connector, lambda item: handled.append(item.id) or True)

    assert result.status == SyncStatus.SUCCESS
    assert result.processed == 1
    assert handled == ["a"]
    assert store.get("fake").value == "c1"


def test_runner_uses_stored_cursor_for_next_fetch():
    store = InMemoryCursorStore()
    store.save(SyncCursor("fake", "old-cursor"))
    connector = FakeConnector([FetchBatch(items=[], next_cursor="old-cursor")])

    result = IncrementalSyncRunner(store, batch_size=7).run(connector, lambda item: True)

    assert connector.calls == [("old-cursor", 7)]
    assert result.cursor_before == "old-cursor"
    assert result.cursor_after == "old-cursor"


def test_runner_isolates_item_handler_errors_and_returns_partial():
    connector = FakeConnector([
        FetchBatch(items=[FetchedItem("ok", {}, "c1"), FetchedItem("bad", {}, "c2")], next_cursor="c2"),
    ])

    def handler(item):
        if item.id == "bad":
            raise RuntimeError("boom")
        return True

    result = IncrementalSyncRunner().run(connector, handler)

    assert result.status == SyncStatus.PARTIAL
    assert result.processed == 1
    assert result.failed == 1
    assert result.issues[0].code == "handler_error"
    assert result.cursor_after == "c2"


def test_runner_does_not_commit_cursor_after_fatal_fetch_error():
    store = InMemoryCursorStore()
    store.save(SyncCursor("fake", "safe"))
    connector = FakeConnector([RuntimeError("api unavailable")])

    result = IncrementalSyncRunner(store).run(connector, lambda item: True)

    assert result.status == SyncStatus.FAILED
    assert result.cursor_after == "safe"
    assert store.get("fake").value == "safe"
    assert result.issues[0].fatal is True


def test_runner_stops_after_max_batches_and_marks_partial():
    connector = FakeConnector([
        FetchBatch(items=[FetchedItem("a", {}, "c1")], next_cursor="c1", has_more=True),
        FetchBatch(items=[FetchedItem("b", {}, "c2")], next_cursor="c2", has_more=True),
    ])

    result = IncrementalSyncRunner(max_batches=1).run(connector, lambda item: True)

    assert result.status == SyncStatus.PARTIAL
    assert result.processed == 1
    assert result.issues[0].code == "max_batches_reached"


def test_runner_counts_skipped_items():
    connector = FakeConnector([FetchBatch(items=[FetchedItem("a", {}, "c1")], next_cursor="c1")])

    result = IncrementalSyncRunner().run(connector, lambda item: False)

    assert result.status == SyncStatus.SUCCESS
    assert result.processed == 0
    assert result.skipped == 1


def test_json_cursor_store_persists_cursor(tmp_path: Path):
    path = tmp_path / "cursors.json"
    store = JsonCursorStore(path)
    store.save(SyncCursor("gmail", "123"))

    reloaded = JsonCursorStore(path).get("gmail")

    assert reloaded is not None
    assert reloaded.connector == "gmail"
    assert reloaded.value == "123"


def test_sync_result_exports_stable_dict():
    connector = FakeConnector([FetchBatch(items=[FetchedItem("a", {}, "c1")], next_cursor="c1")])

    result = IncrementalSyncRunner().run(connector, lambda item: True).to_dict()

    assert result["connector"] == "fake"
    assert result["status"] == "success"
    assert result["ok"] is True
    assert result["processed"] == 1
