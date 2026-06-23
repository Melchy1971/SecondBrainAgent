from pathlib import Path

from secondbrain.desktop.connectors import ConnectorCenterService, ConnectorDescriptor, ConnectorStatus


def _service() -> ConnectorCenterService:
    service = ConnectorCenterService()
    service.register_connector(ConnectorDescriptor("gmail", "Gmail", capabilities=("sync", "import")))
    service.register_connector(ConnectorDescriptor("drive", "Google Drive", capabilities=("sync",)))
    return service


def test_register_and_list_connectors_sorted_by_name():
    service = _service()

    names = [item.descriptor.name for item in service.list_connectors()]

    assert names == ["Gmail", "Google Drive"]


def test_configure_connector_enables_ready_status():
    service = _service()

    config = service.configure("gmail", enabled=True, settings={"label": "INBOX"}, secrets_ref="vault:gmail")
    item = service.list_connectors()[0]

    assert config.enabled is True
    assert item.to_view_model()["enabled"] is True
    assert item.to_view_model()["status"] == ConnectorStatus.READY.value


def test_sync_disabled_connector_is_rejected():
    service = _service()

    result = service.request_sync("gmail")

    assert result.status.value == "rejected"
    assert result.message == "connector is disabled"


def test_sync_enabled_connector_updates_health_to_syncing():
    service = _service()
    service.configure("gmail", enabled=True)

    result = service.request_sync("gmail")
    snapshot = service.health_snapshot()["gmail"]

    assert result.status.value == "accepted"
    assert snapshot["status"] == "syncing"
    assert snapshot["last_sync_at"] is not None


def test_mark_sync_completed_records_items_and_cursor():
    service = _service()
    service.configure("gmail", enabled=True)

    health = service.mark_sync_completed("gmail", items_synced=42, cursor="c2")

    assert health.status == ConnectorStatus.READY
    assert health.items_synced == 42
    assert service.health_snapshot()["gmail"]["cursor"] == "c2"


def test_mark_failed_records_error_without_secret_leak():
    service = _service()
    service.configure("gmail", enabled=True, secrets_ref="vault:gmail-token")

    health = service.mark_failed("gmail", "rate limit")
    view = service.list_connectors()[0].to_view_model()

    assert health.status == ConnectorStatus.FAILED
    assert view["last_error"] == "rate limit"
    assert "vault:gmail-token" not in str(view)


def test_file_store_persists_configuration(tmp_path: Path):
    path = tmp_path / "connectors.json"
    service = ConnectorCenterService.with_file_store(path)
    service.register_connector(ConnectorDescriptor("gmail", "Gmail"))
    service.configure("gmail", enabled=True, settings={"scope": "readonly"}, secrets_ref="vault:gmail")

    restored = ConnectorCenterService.with_file_store(path)
    restored.register_connector(ConnectorDescriptor("gmail", "Gmail"))
    item = restored.list_connectors()[0]

    assert item.config.enabled is True
    assert item.config.settings == {"scope": "readonly"}
    assert item.config.secrets_ref == "vault:gmail"
