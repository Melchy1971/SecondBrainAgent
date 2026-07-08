from secondbrain.connectors.scaffold.transport import FakeTransport
from secondbrain.connectors.google.resources import calendar, contacts, gmail, drive, tasks
from secondbrain.connectors.incremental_runner import IncrementalSyncRunner
from secondbrain.connectors.cursor_store import InMemoryCursorStore


def test_calendar_synctoken_delta_and_runner(config, authed):
    tp = FakeTransport()
    tp.on("GET", "calendars/primary/events", lambda u, m, h, b: tp.json_response(200, {
        "items": [{"id": "e1", "summary": "Meet", "updated": "2026-01-01T00:00:00Z"}], "nextSyncToken": "S1"}))
    _, client = authed(config, tp, {"t": 1000.0})
    conn = calendar.connector(client)
    batch = conn.fetch_since(None, 50)
    assert batch.items[0].payload.external_id == "e1"
    assert batch.next_cursor == "S1"
    store = InMemoryCursorStore()
    IncrementalSyncRunner(store).run(conn, lambda fi: True)
    assert store.get("google_calendar").value == "S1"


def test_contacts_synctoken(config, authed):
    tp = FakeTransport()
    tp.on("GET", "people/me/connections", lambda u, m, h, b: tp.json_response(200, {
        "connections": [{"resourceName": "people/1", "names": [{"displayName": "A"}],
                         "emailAddresses": [{"value": "a@b"}],
                         "metadata": {"sources": [{"updateTime": "2026-01-01T00:00:00Z"}]}}],
        "nextSyncToken": "C1"}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = contacts.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.metadata["emails"] == ["a@b"]
    assert batch.next_cursor == "C1"


def test_gmail_list_then_get_watermark(config, authed):
    tp = FakeTransport()
    tp.on("GET", "gmail/v1/users/me/messages/m1", lambda u, m, h, b: tp.json_response(200, {
        "id": "m1", "internalDate": "1700000000000", "snippet": "hi",
        "payload": {"headers": [{"name": "Subject", "value": "S"}]}}))
    tp.on("GET", "gmail/v1/users/me/messages", lambda u, m, h, b: tp.json_response(200, {"messages": [{"id": "m1"}]}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = gmail.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.external_id == "m1"
    assert batch.next_cursor == str(1700000000)


def test_drive_changes_start_then_delta(config, authed):
    tp = FakeTransport()
    tp.on("GET", "drive/v3/changes/startPageToken", lambda u, m, h, b: tp.json_response(200, {"startPageToken": "100"}))
    tp.on("GET", "drive/v3/changes", lambda u, m, h, b: tp.json_response(200, {
        "changes": [{"file": {"id": "f1", "name": "a.txt", "modifiedTime": "2026-01-01T00:00:00Z"}}],
        "newStartPageToken": "105"}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = drive.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.external_id == "f1"
    assert batch.next_cursor == "105"


def test_tasks_lists_and_watermark(config, authed):
    tp = FakeTransport()
    tp.on("GET", "lists/L1/tasks", lambda u, m, h, b: tp.json_response(200, {
        "items": [{"id": "t1", "title": "Do", "updated": "2026-05-05T00:00:00Z"}]}))
    tp.on("GET", "users/@me/lists", lambda u, m, h, b: tp.json_response(200, {"items": [{"id": "L1"}]}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = tasks.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.external_id == "t1"
    assert batch.next_cursor == "2026-05-05T00:00:00Z"
