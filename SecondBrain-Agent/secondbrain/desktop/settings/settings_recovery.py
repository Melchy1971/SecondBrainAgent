from __future__ import annotations

from .settings_backup import SettingsBackupService
from .settings_integrity import SettingsIntegrityChecker
from .settings_restore import SettingsRestoreService


class SettingsRecoveryService:
    def __init__(
        self,
        backup_service: SettingsBackupService,
        restore_service: SettingsRestoreService,
        integrity: SettingsIntegrityChecker,
    ) -> None:
        self.backup_service = backup_service
        self.restore_service = restore_service
        self.integrity = integrity

    def recover_latest_valid(self) -> dict[str, object]:
        for snapshot in self.backup_service.list_backups():
            report = self.integrity.check_snapshot(snapshot)
            if report.valid:
                self.restore_service.restore(snapshot)
                return {"recovered": True, "snapshot_id": snapshot.snapshot_id}
        return {"recovered": False, "reason": "no_valid_snapshot"}
