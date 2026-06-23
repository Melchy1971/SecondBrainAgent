from __future__ import annotations

import json

from secondbrain.desktop.settings.settings_backup import SettingsBackupService
from secondbrain.desktop.settings.settings_integrity import SettingsIntegrityChecker
from secondbrain.desktop.settings.settings_migration import SettingsMigration, SettingsMigrationService
from secondbrain.desktop.settings.settings_registry import default_settings_registry
from secondbrain.desktop.settings.settings_restore import SettingsRestoreService
from secondbrain.desktop.settings.settings_rollback import SettingsRollbackService
from secondbrain.desktop.settings.settings_recovery import SettingsRecoveryService
from secondbrain.desktop.settings.settings_snapshot import create_snapshot, settings_checksum
from secondbrain.desktop.settings.settings_store import SettingsStore
from secondbrain.desktop.settings.settings_versioning import SettingsVersion, is_compatible


def test_snapshot_checksum_is_stable() -> None:
    left = settings_checksum({"b": 2, "a": 1})
    right = settings_checksum({"a": 1, "b": 2})
    assert left == right


def test_backup_service_creates_and_lists_snapshots(tmp_path) -> None:
    service = SettingsBackupService(tmp_path / "snapshots")
    snapshot = service.create_backup({"desktop.theme": "dark", "general.default_workspace": "default"}, "1.0.0")
    backups = service.list_backups()
    assert backups[0].snapshot_id == snapshot.snapshot_id
    assert service.latest_backup() is not None


def test_integrity_detects_checksum_mismatch() -> None:
    snapshot = create_snapshot({"desktop.theme": "dark", "general.default_workspace": "default"}, "1.0.0")
    broken = type(snapshot)(
        snapshot_id=snapshot.snapshot_id,
        version=snapshot.version,
        created_at=snapshot.created_at,
        checksum="broken",
        settings=snapshot.settings,
        metadata=snapshot.metadata,
    )
    report = SettingsIntegrityChecker(default_settings_registry()).check_snapshot(broken)
    assert report.valid is False
    assert any(issue.code == "checksum_mismatch" for issue in report.issues)


def test_restore_valid_snapshot_to_store(tmp_path) -> None:
    store = SettingsStore(tmp_path / "current.json")
    integrity = SettingsIntegrityChecker(default_settings_registry())
    restore = SettingsRestoreService(store, integrity)
    snapshot = create_snapshot({"desktop.theme": "dark", "general.default_workspace": "default"}, "1.0.0")
    result = restore.restore(snapshot)
    assert result["restored"] is True
    assert store.load()["desktop.theme"] == "dark"


def test_migration_pipeline_applies_registered_steps() -> None:
    service = SettingsMigrationService()
    service.register(SettingsMigration("1.0.0", "1.1.0", lambda data: {**data, "new": True}))
    result = service.migrate({"old": True}, "1.0.0", "1.1.0")
    assert result == {"old": True, "new": True}


def test_recovery_restores_latest_valid_snapshot(tmp_path) -> None:
    registry = default_settings_registry()
    integrity = SettingsIntegrityChecker(registry)
    backup = SettingsBackupService(tmp_path / "snapshots")
    store = SettingsStore(tmp_path / "current.json")
    restore = SettingsRestoreService(store, integrity)
    backup.create_backup({"desktop.theme": "dark", "general.default_workspace": "default"}, "1.0.0")
    result = SettingsRecoveryService(backup, restore, integrity).recover_latest_valid()
    assert result["recovered"] is True
    assert store.load()["desktop.theme"] == "dark"


def test_rollback_uses_previous_snapshot(tmp_path) -> None:
    registry = default_settings_registry()
    integrity = SettingsIntegrityChecker(registry)
    backup = SettingsBackupService(tmp_path / "snapshots")
    store = SettingsStore(tmp_path / "current.json")
    restore = SettingsRestoreService(store, integrity)
    backup.create_backup({"desktop.theme": "light", "general.default_workspace": "default"}, "1.0.0")
    backup.create_backup({"desktop.theme": "dark", "general.default_workspace": "default"}, "1.0.0")
    result = SettingsRollbackService(backup, restore).rollback_to_previous()
    assert result["rolled_back"] is True
    assert store.load()["desktop.theme"] == "light"


def test_version_parse_and_compatibility() -> None:
    assert str(SettingsVersion.parse("2.6")) == "2.6.0"
    assert is_compatible("2.6.1", "2.6.0") is True
    assert is_compatible("3.0.0", "2.6.0") is False
