from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

from .settings_snapshot import VersionedSettingsSnapshot, create_snapshot


class SettingsBackupService:
    def __init__(self, snapshot_dir: Path | str) -> None:
        self.snapshot_dir = Path(snapshot_dir)

    def create_backup(
        self,
        settings: dict[str, Any],
        version: str,
        metadata: dict[str, Any] | None = None,
    ) -> VersionedSettingsSnapshot:
        snapshot = create_snapshot(
            settings=settings, version=version, metadata=metadata
        )
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        latest = self.latest_backup()
        if latest is not None and snapshot.created_at <= latest.created_at:
            snapshot = replace(
                snapshot, created_at=latest.created_at + timedelta(microseconds=1)
            )
        path = self.snapshot_dir / f"{snapshot.snapshot_id}.json"
        path.write_text(
            json.dumps(snapshot.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
        )
        return snapshot

    def list_backups(self) -> list[VersionedSettingsSnapshot]:
        if not self.snapshot_dir.exists():
            return []
        snapshots = [
            VersionedSettingsSnapshot.from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
            for path in self.snapshot_dir.glob("*.json")
        ]
        return sorted(snapshots, key=lambda snapshot: snapshot.created_at, reverse=True)

    def latest_backup(self) -> VersionedSettingsSnapshot | None:
        backups = self.list_backups()
        return backups[0] if backups else None
