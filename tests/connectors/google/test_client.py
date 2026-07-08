def test_google_paging_token_and_synctoken(config, authed):
    from secondbrain.connectors.scaffold.transport import FakeTransport
    tp = FakeTransport()
    state = {"n": 0}
    def handler(u, m, h, b):
        state["n"] += 1
        if "pageToken=P2" in u:
            return tp.json_response(200, {"items": [{"id": "b"}], "nextSyncToken": "SYNC1"})
        return tp.json_response(200, {"items": [{"id": "a"}], "nextPageToken": "P2"})
    tp.on("GET", "calendar/v3/calendars/primary/events", handler)
    _, client = authed(config, tp, {"t": 1000.0})
    items, cursor = client.follow_collection("calendar/v3/calendars/primary/events", delta=True)
    assert [i["id"] for i in items] == ["a", "b"]
    assert cursor == "SYNC1"
    assert state["n"] == 2
