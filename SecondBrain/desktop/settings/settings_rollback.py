from __future__ import annotations

from .settings_backup import SettingsBackupService
from .settings_restore import SettingsRestoreService


class SettingsRollbackService:
    def __init__(self, backup_service: SettingsBackupService, restore_service: SettingsRestoreService) -> None:
        self.backup_service = backup_service
        self.restore_service = restore_service

    def rollback_to_previous(self) -> dict[str, object]:
        backups = self.backup_service.list_backups()
        if len(backups) < 2:
            return {"rolled_back": False, "reason": "no_previous_snapshot"}
        target = backups[1]
        self.restore_service.restore(target)
        return {"rolled_back": True, "snapshot_id": target.snapshot_id}
