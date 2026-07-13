from secondbrain.connectors_v13 import ConnectorRuntimeV13


def test_registry_status(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    assert rt.status()["connectors"] >= 4


def test_enable_and_sync(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    rt.registry.set_enabled("gmail", True)
    result = rt.sync("gmail")
    assert result["ok"] is True
    assert result["run"]["items"] == 1


def test_disabled_connector_blocked(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    result = rt.sync("github")
    assert result["ok"] is False


def test_oauth_token_redacted(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    rt.oauth.store_token("gmail", "secret-token")
    token = rt.oauth.tokens()[0]
    assert "access_token_enc" not in token


def test_webhook_flow(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    rt.webhooks.receive("gmail", "message.created", {"id": "1"})
    assert len(rt.webhooks.list()) == 1
    drained = rt.webhooks.drain()
    assert drained[0]["status"] == "processed"


def test_sync_all_enabled(tmp_path):
    rt = ConnectorRuntimeV13(tmp_path)
    rt.registry.set_enabled("gmail", True)
    rt.registry.set_enabled("github", True)
    results = rt.sync_all()
    assert len(results) == 2
