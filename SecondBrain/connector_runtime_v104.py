from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Any
import json

from .normalizer_v104 import NormalizedRecord, normalize_calendar_event, normalize_document, normalize_email
from .runtime_events_v104 import JsonlEventStore, RuntimeEvent


class Connector(Protocol):
    name: str
    mode: str

    def fetch(self) -> list[dict[str, Any]]: ...
    def normalize(self, item: dict[str, Any]) -> NormalizedRecord: ...


@dataclass
class ConnectorResult:
    connector: str
    fetched: int
    normalized: int
    event_path: str | None
    errors: list[str]


class LocalJsonConnector:
    """Read-only connector for exported JSON fixtures and future API dumps."""

    def __init__(self, name: str, path: Path, record_type: str):
        self.name = name
        self.path = Path(path)
        self.record_type = record_type
        self.mode = "read_only"

    def fetch(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return list(data.get("items", []))
        if isinstance(data, list):
            return data
        raise ValueError(f"Unsupported connector payload in {self.path}")

    def normalize(self, item: dict[str, Any]) -> NormalizedRecord:
        if self.record_type == "email":
            return normalize_email(item, source=self.name)
        if self.record_type == "calendar_event":
            return normalize_calendar_event(item, source=self.name)
        return normalize_document(item, source=self.name)


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        if connector.name in self._connectors:
            raise ValueError(f"Connector already registered: {connector.name}")
        self._connectors[connector.name] = connector

    def names(self) -> list[str]:
        return sorted(self._connectors)

    def get(self, name: str) -> Connector:
        return self._connectors[name]


def sync_connector(connector: Connector, store: JsonlEventStore) -> ConnectorResult:
    errors: list[str] = []
    event_path: Path | None = None
    normalized_count = 0
    try:
        items = connector.fetch()
    except Exception as exc:
        return ConnectorResult(connector.name, 0, 0, None, [f"fetch_failed: {exc}"])

    for item in items:
        try:
            record = connector.normalize(item)
            event = RuntimeEvent(
                event_type="connector.record.normalized",
                source=connector.name,
                actor="connector_runtime",
                risk_level=1,
                payload=record.to_dict(),
            )
            event_path = store.append(event)
            normalized_count += 1
        except Exception as exc:
            errors.append(f"normalize_failed: {exc}")

    return ConnectorResult(connector.name, len(items), normalized_count, str(event_path) if event_path else None, errors)


def sync_all(registry: ConnectorRegistry, store: JsonlEventStore) -> list[ConnectorResult]:
    return [sync_connector(registry.get(name), store) for name in registry.names()]


def registry_from_config(project_root: Path, config: dict[str, Any]) -> ConnectorRegistry:
    registry = ConnectorRegistry()
    for entry in config.get("connectors", []):
        if not entry.get("enabled", True):
            continue
        if entry.get("kind") == "local_json":
            registry.register(LocalJsonConnector(entry["name"], project_root / entry["path"], entry.get("record_type", "document")))
    return registry
