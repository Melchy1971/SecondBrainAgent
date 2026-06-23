from __future__ import annotations

from .settings_integrity import SettingsIntegrityChecker
from .settings_snapshot import VersionedSettingsSnapshot
from .settings_store import SettingsStore


class SettingsRestoreService:
    def __init__(self, store: SettingsStore, integrity: SettingsIntegrityChecker) -> None:
        self.store = store
        self.integrity = integrity

    def restore(self, snapshot: VersionedSettingsSnapshot) -> dict[str, object]:
        report = self.integrity.check_snapshot(snapshot)
        if not report.valid:
            joined = "; ".join(issue.code for issue in report.blocking)
            raise ValueError(f"snapshot integrity failed: {joined}")
        self.store.save(snapshot.settings)
        return {"restored": True, "snapshot_id": snapshot.snapshot_id, "version": snapshot.version}
