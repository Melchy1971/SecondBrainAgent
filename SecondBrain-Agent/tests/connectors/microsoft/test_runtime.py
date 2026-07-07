from secondbrain.connectors.microsoft.config import GraphConfig
from secondbrain.connectors.microsoft.runtime import M365Runtime
from secondbrain.connectors.microsoft.transport import FakeTransport


def _cfg(tmp_path):
    return GraphConfig(
        client_id="test-client", tenant_id="common",
        token_store_path=str(tmp_path / "tok.json"),
        cursor_store_path=str(tmp_path / "cur.json"),
        approval_store_path=str(tmp_path / "app.json"),
    )


def _transport():
    tp = FakeTransport()
    tp.on("POST", "/devicecode", lambda u, m, h, b: tp.json_response(200, {
        "device_code": "DC", "user_code": "WXYZ", "verification_uri": "https://microsoft.com/devicelogin",
        "expires_in": 900, "interval": 1, "message": "enter WXYZ"}))
    tp.on("POST", "/oauth2/v2.0/token", lambda u, m, h, b: tp.json_response(200, {
        "access_token": "AT", "refresh_token": "RT", "expires_in": 3600}))
    tp.on("GET", "me/messages/delta", lambda u, m, h, b: tp.json_response(200, {
        "value": [{"id": "m1", "subject": "Hi", "body": {"content": "b"},
                   "lastModifiedDateTime": "2026-01-01T00:00:00Z"}],
        "@odata.deltaLink": "https://graph.microsoft.com/v1.0/me/messages/delta?$deltatoken=D1"}))
    return tp


def test_login_sync_status_disconnect_cycle(tmp_path):
    tp = _transport()
    rt = M365Runtime(config=_cfg(tmp_path), transport=tp, auto_approve=True)

    login = rt.login(wait=True, sleeper=lambda _s: None)
    assert login["status"] == "ok" and login["authenticated"] is True

    synced = rt.sync(["mail"])
    assert synced["status"] == "ok"
    assert synced["results"]["mail"]["import"]["imported"] == 1
    # item landed in the ingestion sink (memory/knowledge import boundary)
    assert len(rt.sink.jobs) == 1

    status = rt.status()
    assert status["authenticated"] is True
    assert status["cursors"]["mail"].endswith("$deltatoken=D1")
    assert "mail" in status["resources"]

    disc = rt.disconnect()
    assert disc["was_authenticated"] is True
    assert rt.status()["authenticated"] is False


def test_config_error_when_client_id_missing(tmp_path):
    import pytest
    from secondbrain.connectors.microsoft.config import GraphConfigError
    with pytest.raises(GraphConfigError):
        M365Runtime(project_root=str(tmp_path), env={})
