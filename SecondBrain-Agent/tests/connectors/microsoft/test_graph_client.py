from secondbrain.connectors.microsoft.transport import FakeTransport
from secondbrain.connectors.microsoft.graph_client import GraphClient, GraphApiError


def test_paging_follows_nextlink(config, authed):
    tp = FakeTransport()
    def page(url, m, h, b):
        if "skiptoken=2" in url:
            return tp.json_response(200, {"value": [{"id": "c"}]})
        return tp.json_response(200, {"value": [{"id": "a"}, {"id": "b"}],
                                      "@odata.nextLink": config.graph_base_url + "/me/messages?skiptoken=2"})
    tp.on("GET", "me/messages", page)
    _, client = authed(config, tp, {"t": 1000.0})
    items, cursor = client.follow_collection("me/messages")
    assert [i["id"] for i in items] == ["a", "b", "c"]
    assert cursor is None  # non-delta


def test_delta_returns_deltalink_cursor(config, authed):
    tp = FakeTransport()
    tp.on("GET", "me/messages/delta", lambda u, m, h, b: tp.json_response(200, {
        "value": [{"id": "x"}], "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/messages/delta?$deltatoken=D1"}))
    _, client = authed(config, tp, {"t": 1000.0})
    items, cursor = client.follow_collection("me/messages/delta", delta=True)
    assert items[0]["id"] == "x"
    assert cursor.endswith("$deltatoken=D1")


def test_429_retry_after_then_success(config, authed):
    tp = FakeTransport()
    state = {"n": 0}
    def handler(u, m, h, b):
        state["n"] += 1
        if state["n"] == 1:
            return tp.json_response(429, {"error": {"code": "tooManyRequests", "message": "slow"}}, headers={"Retry-After": "0"})
        return tp.json_response(200, {"value": []})
    tp.on("GET", "me/messages", handler)
    _, client = authed(config, tp, {"t": 1000.0})
    client.get("me/messages")
    assert state["n"] == 2


def test_401_triggers_single_reauth_retry(config, authed):
    tp = FakeTransport()
    state = {"g": 0}
    def get_handler(u, m, h, b):
        state["g"] += 1
        if state["g"] == 1:
            return tp.json_response(401, {"error": {"code": "InvalidAuthenticationToken", "message": "expired"}})
        return tp.json_response(200, {"value": [{"id": "ok"}]})
    tp.on("GET", "me/messages", get_handler)
    tp.on("POST", "/oauth2/v2.0/token", lambda u, m, h, b: tp.json_response(200, {
        "access_token": "AT-new", "refresh_token": "RT-2", "expires_in": 3600}))
    _, client = authed(config, tp, {"t": 1000.0})
    data = client.get("me/messages")
    assert data["value"][0]["id"] == "ok"
    assert state["g"] == 2


def test_persistent_500_raises_after_retries(config, authed):
    tp = FakeTransport()
    tp.on("GET", "me/messages", lambda u, m, h, b: tp.json_response(500, {"error": {"code": "x", "message": "boom"}}))
    _, client = authed(config, tp, {"t": 1000.0})
    client.max_retries = 2
    try:
        client.get("me/messages")
        assert False
    except GraphApiError as e:
        assert e.status == 500


def test_batch_chunks_over_20(config, authed):
    tp = FakeTransport()
    seen = {"batches": 0, "sizes": []}
    def batch_handler(u, m, h, b):
        import json
        payload = json.loads(b.decode())
        seen["batches"] += 1
        seen["sizes"].append(len(payload["requests"]))
        return tp.json_response(200, {"responses": [{"id": r["id"], "status": 200, "body": {}} for r in payload["requests"]]})
    tp.on("POST", "$batch", batch_handler)
    _, client = authed(config, tp, {"t": 1000.0})
    reqs = [{"method": "GET", "url": f"/me/messages/{i}"} for i in range(45)]
    responses = client.batch(reqs)
    assert len(responses) == 45
    assert seen["batches"] == 3
    assert seen["sizes"] == [20, 20, 5]
