# PATCH P2.6.4 — Settings Backup, Migration und Recovery

## Inhalt

- Versionierte Settings-Snapshots mit SHA-256-Prüfsumme
- Backup-Service mit Snapshot-Persistenz
- Restore-Service mit Integritätsprüfung
- Migration-Service mit registrierbaren Versionsschritten
- Recovery-Service für letzten gültigen Snapshot
- Rollback-Service auf vorherigen Snapshot
- Version-Kompatibilitätsmodell
- Settings-Events für Backup/Restore/Migration/Recovery/Rollback

## Geänderte/Neue Dateien

- `secondbrain/desktop/settings/settings_snapshot.py`
- `secondbrain/desktop/settings/settings_integrity.py`
- `secondbrain/desktop/settings/settings_backup.py`
- `secondbrain/desktop/settings/settings_restore.py`
- `secondbrain/desktop/settings/settings_migration.py`
- `secondbrain/desktop/settings/settings_recovery.py`
- `secondbrain/desktop/settings/settings_rollback.py`
- `secondbrain/desktop/settings/settings_versioning.py`
- `secondbrain/desktop/settings/settings_events.py`
- `tests/desktop/settings/test_settings_backup_recovery.py`

## Validierung

- `30 passed in 0.34s`

## Ergebnis

P2.6.4 ist implementiert. Settings können versioniert gesichert, geprüft, migriert, wiederhergestellt und zurückgerollt werden.
