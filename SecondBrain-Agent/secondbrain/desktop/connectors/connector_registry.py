from __future__ import annotations

from .connector_models import ConnectorDescriptor


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, ConnectorDescriptor] = {}

    def register(self, descriptor: ConnectorDescriptor) -> None:
        if not descriptor.connector_id.strip():
            raise ValueError("connector_id is required")
        self._connectors[descriptor.connector_id] = descriptor

    def get(self, connector_id: str) -> ConnectorDescriptor | None:
        return self._connectors.get(connector_id)

    def require(self, connector_id: str) -> ConnectorDescriptor:
        descriptor = self.get(connector_id)
        if descriptor is None:
            raise KeyError(f"unknown connector: {connector_id}")
        return descriptor

    def list(self) -> list[ConnectorDescriptor]:
        return sorted(self._connectors.values(), key=lambda item: item.name.lower())

    def ids(self) -> list[str]:
        return sorted(self._connectors)
