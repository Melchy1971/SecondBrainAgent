import json
from secondbrain.connectors.microsoft.transport import FakeTransport
from secondbrain.connectors.microsoft.resources import mail, todo, teams, onenote
from secondbrain.connectors.incremental_runner import IncrementalSyncRunner
from secondbrain.connectors.cursor_store import InMemoryCursorStore


def test_mail_connector_delta_and_runner_commits_cursor(config, authed):
    tp = FakeTransport()
    tp.on("GET", "me/messages/delta", lambda u, m, h, b: tp.json_response(200, {
        "value": [{"id": "m1", "subject": "A", "body": {"content": "x"},
                   "lastModifiedDateTime": "2026-01-01T00:00:00Z"}],
        "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/messages/delta?$deltatoken=D1"}))
    _, client = authed(config, tp, {"t": 1000.0})
    conn = mail.connector(client)
    batch = conn.fetch_since(None, 50)
    assert len(batch.items) == 1
    assert batch.items[0].payload.external_id == "m1"
    assert batch.next_cursor.endswith("$deltatoken=D1")

    store = InMemoryCursorStore()
    runner = IncrementalSyncRunner(store)
    seen = []
    result = runner.run(conn, lambda fi: seen.append(fi.payload.external_id) or True)
    assert result.processed == 1
    assert store.get("m365_mail").value.endswith("$deltatoken=D1")


def test_todo_connector_multilist_cursor_is_json(config, authed):
    tp = FakeTransport()
    # register the more specific route first (FakeTransport matches by substring order)
    tp.on("GET", "me/todo/lists/L1/tasks/delta", lambda u, m, h, b: tp.json_response(200, {
        "value": [{"id": "task1", "title": "T", "lastModifiedDateTime": "2026-01-01T00:00:00Z"}],
        "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/todo/lists/L1/tasks/delta?$deltatoken=T1"}))
    tp.on("GET", "me/todo/lists?", lambda u, m, h, b: tp.json_response(200, {"value": [{"id": "L1"}]}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = todo.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.external_id == "task1"
    cursor_map = json.loads(batch.next_cursor)
    assert "L1" in cursor_map and cursor_map["L1"].endswith("$deltatoken=T1")


def test_teams_connector_uses_batch_and_watermark(config, authed):
    tp = FakeTransport()
    tp.on("GET", "me/chats", lambda u, m, h, b: tp.json_response(200, {"value": [{"id": "chatA"}]}))
    def batch_handler(u, m, h, b):
        payload = json.loads(b.decode())
        resps = [{"id": r["id"], "status": 200, "body": {"value": [
            {"id": "msg1", "body": {"content": "hello"}, "from": {"user": {"displayName": "Ann"}},
             "lastModifiedDateTime": "2026-02-02T00:00:00Z"}]}} for r in payload["requests"]]
        return tp.json_response(200, {"responses": resps})
    tp.on("POST", "$batch", batch_handler)
    _, client = authed(config, tp, {"t": 1000.0})
    batch = teams.connector(client).fetch_since(None, 10)
    assert batch.items[0].payload.external_id == "msg1"
    assert batch.next_cursor == "2026-02-02T00:00:00Z"


def test_onenote_watermark_non_delta(config, authed):
    tp = FakeTransport()
    tp.on("GET", "me/onenote/pages", lambda u, m, h, b: tp.json_response(200, {
        "value": [{"id": "p1", "title": "One", "lastModifiedDateTime": "2026-03-03T00:00:00Z"}]}))
    _, client = authed(config, tp, {"t": 1000.0})
    batch = onenote.connector(client).fetch_since(None, 50)
    assert batch.items[0].payload.source == "m365_onenote"
    assert batch.next_cursor == "2026-03-03T00:00:00Z"
