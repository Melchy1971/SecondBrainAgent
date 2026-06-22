from secondbrain.connector_framework import ConnectorFrameworkRuntime


def test_migrate_status(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    rt.migrate()
    assert rt.status()["connectors"] == 6


def test_enable_sync(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    rt.enable("gmail")
    result = rt.sync("gmail")
    assert result["ok"] is True
    assert result["items"] == 1


def test_disabled_blocks(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    result = rt.sync("github")
    assert result["ok"] is False


def test_sync_all(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    rt.enable("gmail")
    rt.enable("github")
    results = rt.sync_all()
    assert len(results) == 2


def test_items_and_cursor(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    rt.enable("paperless")
    rt.sync("paperless")
    assert rt.items("paperless")
    assert rt.cursor("paperless")["cursor"] is not None


def test_token_redacted(tmp_path):
    rt = ConnectorFrameworkRuntime(tmp_path)
    token = rt.token_store("gmail", "secret-token")
    assert token["token_ref"] == "***REDACTED***"
