from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.operations_v119 import OperationsEngine


class BackupCenterViewModel:
    """UI-neutral adapter for the native Backup and Restore Center."""

    def __init__(
        self,
        project_root: str | Path,
        runtime_dir: str | Path | None = None,
        *,
        operations: OperationsEngine | None = None,
    ) -> None:
        root = Path(project_root).resolve()
        self.operations = operations or OperationsEngine(root, runtime_dir or root / "runtime")

    def snapshot(self) -> dict[str, Any]:
        history = self.operations.backups.list(50)
        health = self.operations.backup_health()
        return {
            "schema": "secondbrain.gui.backup_center.v30_96",
            "backup_center": {
                "status": health["status"],
                "backup_count": health["backup_count"],
                "encryption_ready": self.operations.backups.encryption_configured,
                "latest_backup": history[-1] if history else None,
            },
            "restore_center": self.operations.restore_wizard.status(),
            "history": list(reversed(history)),
            "scheduler": self.operations.backup_scheduler.status(),
            "health": health,
            "actions": [
                "create_backup",
                "validate_backup",
                "restore_dry_run",
                "restore",
                "rollback_restore",
                "configure_schedule",
            ],
        }

    def create_backup(
        self,
        *,
        label: str | None = None,
        include_runtime: bool = True,
        include_database: bool = True,
        encrypt: bool | None = None,
    ) -> dict[str, Any]:
        return self.operations.create_backup(
            include_runtime,
            label,
            encrypt=encrypt,
            include_database=include_database,
        )

    def validate_backup(self, backup: str) -> dict[str, Any]:
        return self.operations.backups.verify(backup)

    def restore_dry_run(self, backup: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        return self.operations.restore_wizard.dry_run(backup, target_dir)

    def restore(self, backup: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        return self.operations.restore_wizard.restore(backup, target_dir)

    def rollback_restore(self) -> dict[str, Any]:
        return self.operations.restore_wizard.rollback()

    def configure_schedule(self, interval: str = "daily", *, enabled: bool = True) -> dict[str, Any]:
        return self.operations.backup_scheduler.configure(interval=interval, enabled=enabled)

