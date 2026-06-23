from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .connector_models import ConnectorConfig
from .connector_registry import ConnectorRegistry


class ConfigFieldType(str, Enum):
    TEXT = "text"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    SELECT = "select"
    SECRET = "secret"


@dataclass(frozen=True)
class ConnectorConfigField:
    name: str
    label: str
    field_type: ConfigFieldType = ConfigFieldType.TEXT
    required: bool = False
    default: Any = None
    options: tuple[str, ...] = ()
    min_value: int | None = None
    max_value: int | None = None

    def validate(self, value: Any) -> Any:
        if value is None or value == "":
            if self.required and self.default is None:
                raise ConnectorConfigurationError(f"Missing required field: {self.name}")
            return self.default
        if self.field_type == ConfigFieldType.TEXT:
            return str(value)
        if self.field_type == ConfigFieldType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.lower() in {"true", "1", "yes", "on"}:
                return True
            if isinstance(value, str) and value.lower() in {"false", "0", "no", "off"}:
                return False
            raise ConnectorConfigurationError(f"Invalid boolean field: {self.name}")
        if self.field_type == ConfigFieldType.INTEGER:
            try:
                number = int(value)
            except (TypeError, ValueError) as exc:
                raise ConnectorConfigurationError(f"Invalid integer field: {self.name}") from exc
            if self.min_value is not None and number < self.min_value:
                raise ConnectorConfigurationError(f"Field below minimum: {self.name}")
            if self.max_value is not None and number > self.max_value:
                raise ConnectorConfigurationError(f"Field above maximum: {self.name}")
            return number
        if self.field_type == ConfigFieldType.SELECT:
            text = str(value)
            if self.options and text not in self.options:
                raise ConnectorConfigurationError(f"Invalid option for field: {self.name}")
            return text
        if self.field_type == ConfigFieldType.SECRET:
            text = str(value)
            if not text.startswith("secret://"):
                raise ConnectorConfigurationError(f"Secret fields must use secret:// references: {self.name}")
            return text
        return value


@dataclass(frozen=True)
class ConnectorConfigurationSchema:
    connector_id: str
    fields: tuple[ConnectorConfigField, ...] = ()

    def validate_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        allowed = {field.name for field in self.fields}
        unknown = sorted(set(settings) - allowed)
        if unknown:
            raise ConnectorConfigurationError(f"Unknown config fields: {', '.join(unknown)}")
        return {field.name: field.validate(settings.get(field.name)) for field in self.fields if field.validate(settings.get(field.name)) is not None}


class ConnectorConfigurationError(ValueError):
    pass


@dataclass
class ConnectorConfigurationRegistry:
    _schemas: dict[str, ConnectorConfigurationSchema] = field(default_factory=dict)

    def register(self, schema: ConnectorConfigurationSchema) -> None:
        if not schema.connector_id:
            raise ConnectorConfigurationError("connector_id is required")
        self._schemas[schema.connector_id] = schema

    def require(self, connector_id: str) -> ConnectorConfigurationSchema:
        try:
            return self._schemas[connector_id]
        except KeyError as exc:
            raise ConnectorConfigurationError(f"No configuration schema registered for connector: {connector_id}") from exc

    def get(self, connector_id: str) -> ConnectorConfigurationSchema | None:
        return self._schemas.get(connector_id)


class ConnectorConfigurationService:
    def __init__(self, connector_registry: ConnectorRegistry, schema_registry: ConnectorConfigurationRegistry | None = None) -> None:
        self.connector_registry = connector_registry
        self.schema_registry = schema_registry or ConnectorConfigurationRegistry()

    def build_config(
        self,
        connector_id: str,
        *,
        enabled: bool,
        settings: dict[str, Any] | None = None,
        secrets_ref: str | None = None,
    ) -> ConnectorConfig:
        self.connector_registry.require(connector_id)
        schema = self.schema_registry.get(connector_id)
        validated_settings = schema.validate_settings(settings or {}) if schema else dict(settings or {})
        if secrets_ref is not None and not (secrets_ref.startswith("secret://") or secrets_ref.startswith("vault:")):
            raise ConnectorConfigurationError("secrets_ref must use a secret:// or vault: reference")
        return ConnectorConfig(
            connector_id=connector_id,
            enabled=bool(enabled),
            settings=validated_settings,
            secrets_ref=secrets_ref,
        )

    def enable(self, config: ConnectorConfig) -> ConnectorConfig:
        return ConnectorConfig(
            connector_id=config.connector_id,
            enabled=True,
            settings=dict(config.settings),
            secrets_ref=config.secrets_ref,
        )

    def disable(self, config: ConnectorConfig) -> ConnectorConfig:
        return ConnectorConfig(
            connector_id=config.connector_id,
            enabled=False,
            settings=dict(config.settings),
            secrets_ref=config.secrets_ref,
        )

    def sanitized_view(self, config: ConnectorConfig) -> dict[str, Any]:
        return config.sanitized()
