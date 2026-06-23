from __future__ import annotations

import pytest

from secondbrain.desktop.connectors.connector_center_service import ConnectorCenterService
from secondbrain.desktop.connectors.connector_configuration import (
    ConfigFieldType,
    ConnectorConfigField,
    ConnectorConfigurationError,
    ConnectorConfigurationRegistry,
    ConnectorConfigurationSchema,
    ConnectorConfigurationService,
)
from secondbrain.desktop.connectors.connector_models import ConnectorDescriptor, ConnectorStatus
from secondbrain.desktop.connectors.connector_registry import ConnectorRegistry


def _registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(ConnectorDescriptor(connector_id="drive", name="Google Drive"))
    return registry


def _schema_registry() -> ConnectorConfigurationRegistry:
    schemas = ConnectorConfigurationRegistry()
    schemas.register(
        ConnectorConfigurationSchema(
            connector_id="drive",
            fields=(
                ConnectorConfigField("folder", "Folder", required=True),
                ConnectorConfigField("recursive", "Recursive", ConfigFieldType.BOOLEAN, default=True),
                ConnectorConfigField("limit", "Limit", ConfigFieldType.INTEGER, default=100, min_value=1, max_value=500),
                ConnectorConfigField("mode", "Mode", ConfigFieldType.SELECT, default="delta", options=("delta", "full")),
                ConnectorConfigField("token", "Token", ConfigFieldType.SECRET, required=True),
            ),
        )
    )
    return schemas


def test_configuration_service_validates_and_coerces_settings() -> None:
    service = ConnectorConfigurationService(_registry(), _schema_registry())

    config = service.build_config(
        "drive",
        enabled=True,
        settings={"folder": "Inbox", "recursive": "false", "limit": "25", "mode": "full", "token": "secret://drive/token"},
        secrets_ref="secret://drive/oauth",
    )

    assert config.enabled is True
    assert config.settings == {"folder": "Inbox", "recursive": False, "limit": 25, "mode": "full", "token": "secret://drive/token"}
    assert config.sanitized()["secrets_ref"] == "configured"


def test_configuration_rejects_unknown_and_invalid_fields() -> None:
    service = ConnectorConfigurationService(_registry(), _schema_registry())

    with pytest.raises(ConnectorConfigurationError, match="Unknown config fields"):
        service.build_config("drive", enabled=True, settings={"unknown": "x"})

    with pytest.raises(ConnectorConfigurationError, match="Secret fields"):
        service.build_config("drive", enabled=True, settings={"folder": "x", "token": "plain"})

    with pytest.raises(ConnectorConfigurationError, match="above maximum"):
        service.build_config("drive", enabled=True, settings={"folder": "x", "limit": 999, "token": "secret://x"})


def test_center_service_uses_configuration_schema_and_toggle_flows(tmp_path) -> None:
    registry = _registry()
    configuration_service = ConnectorConfigurationService(registry, _schema_registry())
    center = ConnectorCenterService.with_file_store(tmp_path / "connectors.json")
    center.registry = registry
    center.configuration_service = configuration_service
    center.register_connector(ConnectorDescriptor(connector_id="drive", name="Google Drive"))

    config = center.configure("drive", enabled=True, settings={"folder": "Inbox", "token": "secret://token"})
    assert config.settings["recursive"] is True
    assert center.list_connectors()[0].health.status is ConnectorStatus.READY

    disabled = center.disable_connector("drive")
    assert disabled.enabled is False
    assert center.health_snapshot()["drive"]["status"] == "disabled"

    enabled = center.enable_connector("drive")
    assert enabled.enabled is True
    assert center.health_snapshot()["drive"]["status"] == "ready"
