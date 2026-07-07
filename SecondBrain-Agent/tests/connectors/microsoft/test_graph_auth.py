import json
from secondbrain.connectors.microsoft.graph_auth import GraphAuthenticator, GraphAuthError
from secondbrain.connectors.microsoft.transport import FakeTransport


def _auth(config, transport, t=1000.0):
    return GraphAuthenticator(config, transport=transport, clock=lambda: t)


def test_device_login_flow_pending_then_ok(config):
    tp = FakeTransport()
    tp.on("POST", "/devicecode", lambda u, m, h, b: tp.json_response(200, {
        "device_code": "DC", "user_code": "ABCD-EFGH",
        "verification_uri": "https://microsoft.com/devicelogin",
        "expires_in": 900, "interval": 1, "message": "enter ABCD-EFGH"}))
    state = {"n": 0}
    def token_handler(u, m, h, b):
        state["n"] += 1
        if state["n"] < 2:
            return tp.json_response(400, {"error": "authorization_pending"})
        return tp.json_response(200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600})
    tp.on("POST", "/oauth2/v2.0/token", token_handler)

    auth = _auth(config, tp)
    start = auth.begin_device_login()
    assert start.user_code == "ABCD-EFGH"
    assert "device_code" not in start.to_public_dict()  # secret not leaked
    token = auth.complete_device_login(start, sleeper=lambda _s: None)
    assert token["access_token"] == "AT"
    assert auth.is_authenticated()
    # persisted with expires_at
    saved = auth.token_repo.load_all()["m365"]
    assert saved["expires_at"] == 1000.0 + 3600


def test_refresh_preserves_refresh_token_when_omitted(config):
    tp = FakeTransport()
    tp.on("POST", "/oauth2/v2.0/token", lambda u, m, h, b: tp.json_response(200, {
        "access_token": "AT2", "expires_in": 3600}))  # no refresh_token in response
    auth = _auth(config, tp)
    auth.token_repo.save("m365", {"access_token": "old", "refresh_token": "RT-keep", "expires_at": 0})
    token = auth.refresh("RT-keep")
    assert token["access_token"] == "AT2"
    assert token["refresh_token"] == "RT-keep"


def test_access_token_refreshes_when_near_expiry(config):
    tp = FakeTransport()
    tp.on("POST", "/oauth2/v2.0/token", lambda u, m, h, b: tp.json_response(200, {
        "access_token": "FRESH", "refresh_token": "RT2", "expires_in": 3600}))
    auth = _auth(config, tp)
    auth.token_repo.save("m365", {"access_token": "STALE", "refresh_token": "RT", "expires_at": 1000.0 + 10})
    assert auth.access_token() == "FRESH"  # within 300s refresh window


def test_access_token_without_session_raises(config):
    auth = _auth(config, FakeTransport())
    try:
        auth.access_token()
        assert False
    except GraphAuthError as e:
        assert "not authenticated" in str(e)


def test_forget_removes_token(config):
    auth = _auth(config, FakeTransport())
    auth.token_repo.save("m365", {"access_token": "AT", "expires_at": 0})
    assert auth.forget() is True
    assert auth.is_authenticated() is False
