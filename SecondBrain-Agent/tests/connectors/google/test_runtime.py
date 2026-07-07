from secondbrain.connectors.google.config import GoogleConfig
from secondbrain.connectors.google.runtime import GoogleRuntime
from secondbrain.connectors.scaffold.transport import FakeTransport


def _cfg(tmp_path):
    return GoogleConfig(client_id="cid", client_secret="csecret",
                        token_store_path=str(tmp_path / "t.json"),
                        cursor_store_path=str(tmp_path / "c.json"),
                        approval_store_path=str(tmp_path / "a.json"))


def _tp():
    tp = FakeTransport()
    tp.on("POST", "/device/code", lambda u, m, h, b: tp.json_response(200, {
        "device_code": "DC", "user_code": "WXYZ", "verification_url": "https://g/device",
        "expires_in": 900, "interval": 1}))
    tp.on("POST", "/token", lambda u, m, h, b: tp.json_response(200, {
        "access_token": "AT", "refresh_token": "RT", "expires_in": 3600}))
    tp.on("GET", "calendars/primary/events", lambda u, m, h, b: tp.json_response(200, {
        "items": [{"id": "e1", "summary": "Meet", "updated": "2026-01-01T00:00:00Z"}], "nextSyncToken": "S1"}))
    return tp


def test_google_login_sync_status_disconnect(tmp_path):
    tp = _tp()
    rt = GoogleRuntime(config=_cfg(tmp_path), transport=tp, auto_approve=True)
    assert rt.login(wait=True, sleeper=lambda _s: None)["status"] == "ok"
    synced = rt.sync(["calendar"])
    assert synced["results"]["calendar"]["import"]["imported"] == 1
    assert len(rt.sink.jobs) == 1
    status = rt.status()
    assert status["authenticated"] and status["cursors"]["calendar"] == "S1"
    assert rt.disconnect()["was_authenticated"] is True


def test_config_error(tmp_path):
    import pytest
    from secondbrain.connectors.google.config import GoogleConfigError
    with pytest.raises(GoogleConfigError):
        GoogleRuntime(project_root=str(tmp_path), env={})
