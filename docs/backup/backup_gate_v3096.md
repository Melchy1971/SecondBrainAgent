# Backup/Restore v30.96 – Delta-Analyse und Gate

## Ergebnis der Bestandsaufnahme

Das Backup-/Restore-System aus Prompt 35 ist auf `main` (`9149839`) **bereits
vollständig implementiert**. Kein Neubau nötig.

Kernmodul: `SecondBrain/operations_v119.py` (906 Zeilen), `BackupManager` +
`BackupManifest` (Schema `secondbrain.backup.manifest.v30_96`). Krypto:
`SecondBrain/vault/crypto.py` (AES-256-GCM). Verdrahtung: `launcher.py`
`ops-backup`, `ops-backups`, `ops-backup-verify`, `ops-backup-health`,
`ops-backup-report`, `ops-backup-schedule-configure/run`, `ops-restore-plan`,
`ops-restore`, `ops-restore-rollback`. GUI: `SecondBrain/gui/backup_center.py`.
Tests: `tests/test_backup_restore_v3096.py`, `tests/integration/test_backup_restore.py`.

### Abnahmekriterien-Abdeckung (Bestand)

| # | Kriterium | Abgedeckt durch |
| --- | --- | --- |
| 1 | vollständiges Backup | `BackupManager.create`, `test_encrypted_versioned_backup_covers_governed_components` |
| 2 | Checksums geprüft | `verify` + `_sha256` je Datei, `test_restore_roundtrip_validates_every_file` |
| 3 | manipuliertes Backup blockiert | `test_corrupted_encrypted_backup_is_rejected_without_target_mutation` |
| 4 | falscher Schlüssel blockiert | AES-GCM `InvalidTag` (operations_v119:388) |
| 5 | Restore vollständig | `restore`, `test_restore_roundtrip...` |
| 6 | Teil-Restore | `restore_plan`/`restore` je Komponente (`_component_files`) |
| 7 | Rollback bei Fehler | `rollback` (lossless), `test_...rollback_is_lossless` |
| 8 | pgvector nach Restore | `_postgres_dump`, `test_postgres_and_pgvector_dump_is_included_without_dsn_leak` |
| 9 | Approval-/Audit-Historie erhalten | governed components im Backup-Set |
| 10 | Restore-Bericht | `restore`/`verify` liefern Report; `health`/`report` secret-frei |

Verschlüsselung (AES-256-GCM), Manifest ohne Secrets, Hash je Datei,
Manipulationserkennung, kontrollierter Fehler bei falschem Key, Retention über
`scheduled_backup` – alles vorhanden.

## Echtes Delta: `backup-gate`

Fehlend war ausschließlich das **aggregierte Gate** (PASS/CONDITIONAL_PASS/
BLOCKED über die Backup-Invarianten), analog zu `security-gate`. Vorhanden waren
nur Einzel-Kommandos (`ops-backup-verify` etc.).

Neu (dünne Schicht, **kein** Nachbau des Managers):
`SecondBrain/backup_gate_v3096.py` – `run_backup_gate(project_root, manager=None)`
treibt den bestehenden `BackupManager` durch create → checksums → tamper →
wrong-key → restore-dry-run → rollback → no-secrets und benotet PASS/
CONDITIONAL_PASS/BLOCKED. Import-sicher (lazy Import von `BackupManager`, damit
`cryptography`/PostgreSQL nicht beim Import gezogen werden) und per Dependency-
Injection isoliert testbar.

Tests: `tests/test_backup_gate_v3096.py` (7 grün, Fake-Manager) verifizieren die
Gate-Entscheidungslogik ohne Laufzeit.

### Launcher-Anschluss

Standalone bereits nutzbar: `python -m secondbrain.backup_gate_v3096`.

Für das exakte Kommando `python launcher.py backup-gate` genügt in `launcher.py`:

```python
# in der sub.add_parser-Liste:
sub.add_parser("backup-gate")

# im Dispatch (analog zu security-gate):
if cmd == "backup-gate":
    from secondbrain.backup_gate_v3096 import run_backup_gate, PASS, CONDITIONAL_PASS
    report = run_backup_gate(args.project_root_option or ".")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in (PASS, CONDITIONAL_PASS) else 1
```

Diesen 2-Zeilen-Anschluss habe ich bewusst **nicht** blind in die 1113-Zeilen-
`launcher.py` geschrieben, weil ich den Import hier nicht ausführen/verifizieren
kann und ein ungetesteter Eingriff in den zentralen Dispatch gegen „keine
halbfertigen Änderungen" verstößt.

## Restrisiken

1. `run_backup_gate` mit echtem `BackupManager` erfordert `cryptography` +
   PostgreSQL und wurde in dieser Session nicht live ausgeführt; isoliert
   getestet ist die Entscheidungslogik (7 grün).
2. Der Launcher-Anschluss (`backup-gate`) ist als exakter Patch dokumentiert,
   aber nicht eingespielt – bitte lokal ergänzen und `python launcher.py
   backup-gate` einmal gegen ein echtes Backup laufen lassen.
3. Live-Verifikation gehört auf deine Maschine:
   `python -m pytest -q tests/test_backup_restore_v3096.py tests/integration/test_backup_restore.py`.
