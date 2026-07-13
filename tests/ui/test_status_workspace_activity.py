import pytest
from secondbrain.ui.status_bar import StatusBarModel
from secondbrain.ui.workspace_selector import WorkspaceSelectorModel
from secondbrain.ui.activity_feed import ActivityFeedModel


def test_status_bar_segments():
    m = StatusBarModel(workspace="proj", connection="online", active_jobs=2, unread_notifications=3)
    ids = [s["id"] for s in m.segments()]
    assert ids == ["workspace", "connection", "jobs", "notifications"]
    conn = next(s for s in m.segments() if s["id"] == "connection")
    assert conn["role"] == "success"


def test_workspace_selector():
    ws = WorkspaceSelectorModel(["a", "b"], "a")
    ws.add("c"); assert ws.list() == ["a", "b", "c"]
    assert ws.switch("b") == "b"
    with pytest.raises(ValueError):
        ws.switch("z")


def test_activity_feed_capacity_and_filter():
    feed = ActivityFeedModel(capacity=3)
    for i in range(5):
        feed.add("sync", f"e{i}", severity="info" if i % 2 else "warning")
    assert len(feed.recent(10)) == 3            # capped
    assert feed.recent(1)[0]["text"] == "e4"    # newest first
    assert all(e["kind"] == "sync" for e in feed.by_kind("sync"))
    assert feed.by_severity("warning")
