from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class VersionedSettingsSnapshot:
    snapshot_id: str
    version: str
    created_at: datetime
    checksum: str
    settings: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
            "settings": self.settings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VersionedSettingsSnapshot":
        return cls(
            snapshot_id=str(data["snapshot_id"]),
            version=str(data["version"]),
            created_at=datetime.fromisoformat(str(data["created_at"])),
            checksum=str(data["checksum"]),
            settings=dict(data.get("settings", {})),
            metadata=dict(data.get("metadata", {})),
        )


def settings_checksum(settings: dict[str, Any]) -> str:
    payload = json.dumps(settings, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_snapshot(
    settings: dict[str, Any],
    version: str,
    metadata: dict[str, Any] | None = None,
    snapshot_id: str | None = None,
) -> VersionedSettingsSnapshot:
    normalized = dict(settings)
    return VersionedSettingsSnapshot(
        snapshot_id=snapshot_id or uuid4().hex,
        version=version,
        created_at=datetime.now(timezone.utc),
        checksum=settings_checksum(normalized),
        settings=normalized,
        metadata=dict(metadata or {}),
    )
