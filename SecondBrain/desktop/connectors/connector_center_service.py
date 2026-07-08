from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .connector_actions import ConnectorActionResult, ConnectorActionService
from .connector_config_store import ConnectorConfigStore
from .connector_configuration import ConnectorConfigurationService
from .connector_models import ConnectorConfig, ConnectorDescriptor, ConnectorHealth, ConnectorStatus, utcnow
from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class ConnectorCenterItem:
    descriptor: ConnectorDescriptor
    config: ConnectorConfig
    health: ConnectorHealth

    def to_view_model(self) -> dict[str, Any]:
        return {
            "connector_id": self.descriptor.connector_id,
            "name": self.descriptor.name,
            "description": self.descriptor.description,
            "capabilities": list(self.descriptor.capabilities),
            "enabled": self.config.enabled,
            "status": self.health.status.value,
            "last_sync_at": self.health.snapshot()["last_sync_at"],
            "last_error": self.health.last_error,
            "items_synced": self.health.items_synced,
        }


class ConnectorCenterService:
    def __init__(
        self,
        registry: ConnectorRegistry | None = None,
        config_store: ConnectorConfigStore | None = None,
        action_service: ConnectorActionService | None = None,
        configuration_service: ConnectorConfigurationService | None = None,
    ) -> None:
        self.registry = registry or ConnectorRegistry()
        self.config_store = config_store
        self.action_service = action_service or ConnectorActionService()
        self.configuration_service = configuration_service or ConnectorConfigurationService(self.registry)
        self._configs: dict[str, ConnectorConfig] = config_store.load_all() if config_store else {}
        self._health: dict[str, ConnectorHealth] = {}

    @classmethod
    def with_file_store(cls, path: str | Path) -> "ConnectorCenterService":
        return cls(config_store=ConnectorConfigStore(path))

    def register_connector(self, descriptor: ConnectorDescriptor) -> None:
        self.registry.register(descriptor)
        self._configs.setdefault(descriptor.connector_id, ConnectorConfig(connector_id=descriptor.connector_id))
        self._health.setdefault(descriptor.connector_id, ConnectorHealth(connector_id=descriptor.connector_id, status=ConnectorStatus.DISABLED))

    def configure(self, connector_id: str, *, enabled: bool, settings: dict[str, Any] | None = None, secrets_ref: str | None = None) -> ConnectorConfig:
        self.registry.require(connector_id)
        config = self.configuration_service.build_config(
            connector_id,
            enabled=enabled,
            settings=settings or {},
            secrets_ref=secrets_ref,
        )
        self._configs[connector_id] = config
        self._health[connector_id] = ConnectorHealth(connector_id=connector_id, status=ConnectorStatus.READY if enabled else ConnectorStatus.DISABLED)
        self._persist()
        return config

    def enable_connector(self, connector_id: str) -> ConnectorConfig:
        self.registry.require(connector_id)
        current = self._configs.get(connector_id, ConnectorConfig(connector_id=connector_id))
        config = self.configuration_service.enable(current)
        self._configs[connector_id] = config
        self._health[connector_id] = ConnectorHealth(connector_id=connector_id, status=ConnectorStatus.READY)
        self._persist()
        return config

    def disable_connector(self, connector_id: str) -> ConnectorConfig:
        self.registry.require(connector_id)
        current = self._configs.get(connector_id, ConnectorConfig(connector_id=connector_id))
        config = self.configuration_service.disable(current)
        self._configs[connector_id] = config
        self._health[connector_id] = ConnectorHealth(connector_id=connector_id, status=ConnectorStatus.DISABLED)
        self._persist()
        return config

    def list_connectors(self) -> list[ConnectorCenterItem]:
        return [self._item(descriptor.connector_id) for descriptor in self.registry.list()]

    def health_snapshot(self) -> dict[str, dict[str, Any]]:
        return {item.descriptor.connector_id: item.health.snapshot() for item in self.list_connectors()}

    def request_sync(self, connector_id: str) -> ConnectorActionResult:
        self.registry.require(connector_id)
        config = self._configs.get(connector_id, ConnectorConfig(connector_id=connector_id))
        result = self.action_service.sync(connector_id, config.enabled)
        if result.status.value == "accepted":
            self._health[connector_id] = ConnectorHealth(
                connector_id=connector_id,
                status=ConnectorStatus.SYNCING,
                last_sync_at=utcnow(),
                items_synced=self._health.get(connector_id, ConnectorHealth.ready(connector_id)).items_synced,
            )
        return result

    def mark_sync_completed(self, connector_id: str, *, items_synced: int, cursor: str | None = None) -> ConnectorHealth:
        self.registry.require(connector_id)
        health = ConnectorHealth(
            connector_id=connector_id,
            status=ConnectorStatus.READY,
            last_sync_at=utcnow(),
            items_synced=items_synced,
            cursor=cursor,
        )
        self._health[connector_id] = health
        return health

    def mark_failed(self, connector_id: str, error: str) -> ConnectorHealth:
        self.registry.require(connector_id)
        health = ConnectorHealth(
            connector_id=connector_id,
            status=ConnectorStatus.FAILED,
            last_error=error,
        )
        self._health[connector_id] = health
        return health

    def _item(self, connector_id: str) -> ConnectorCenterItem:
        descriptor = self.registry.require(connector_id)
        config = self._configs.get(connector_id, ConnectorConfig(connector_id=connector_id))
        health = self._health.get(connector_id, ConnectorHealth(connector_id=connector_id, status=ConnectorStatus.DISABLED))
        return ConnectorCenterItem(descriptor=descriptor, config=config, health=health)

    def _persist(self) -> None:
        if self.config_store:
            self.config_store.save_all(self._configs)
