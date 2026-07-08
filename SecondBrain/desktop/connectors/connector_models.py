from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ConnectorStatus(str, Enum):
    DISABLED = "disabled"
    READY = "ready"
    SYNCING = "syncing"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True)
class ConnectorConfig:
    connector_id: str
    enabled: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    secrets_ref: str | None = None

    def sanitized(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "enabled": self.enabled,
            "settings": dict(self.settings),
            "secrets_ref": "configured" if self.secrets_ref else None,
        }


@dataclass(frozen=True)
class ConnectorDescriptor:
    connector_id: str
    name: str
    description: str = ""
    capabilities: tuple[str, ...] = ()
    configurable: bool = True


@dataclass(frozen=True)
class ConnectorHealth:
    connector_id: str
    status: ConnectorStatus
    last_sync_at: datetime | None = None
    last_error: str | None = None
    items_synced: int = 0
    cursor: str | None = None

    @classmethod
    def ready(cls, connector_id: str) -> "ConnectorHealth":
        return cls(connector_id=connector_id, status=ConnectorStatus.READY)

    def snapshot(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "status": self.status.value,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_error": self.last_error,
            "items_synced": self.items_synced,
            "cursor": self.cursor,
        }


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
