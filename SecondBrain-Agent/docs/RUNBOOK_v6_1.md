# Runbook v6.1 Production Hardening

## Standardprüfung

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\runtime_diagnostics.py
python scripts\backup_restore_test.py
python scripts\run_hardening_tests.py
python scripts\release_gate.py
```

## Bewertung

```text
PASS    releasefähig
BLOCKED nicht releasefähig
```

## Pflichtbedingungen

- Vault existiert
- Inbox existiert
- Kernordner existieren
- keine Secret Findings
- Smoke Tests laufen
- Backup Restore Test läuft
- destruktive Aktionen deaktiviert
- E-Mail-Versand deaktiviert

## Fehlerbehebung

### Vault fehlt

`config/settings.yaml` prüfen.

### Backup Restore FAIL

Schreibrechte auf `SecondBrain-Agent/backups` prüfen.

### Secret Scan FAIL

API-Key aus Markdown entfernen und in `config/secrets.local.yaml` verschieben.

### Quality Gate WARNING

Quality Report prüfen und Frontmatter/Tags/Titel ergänzen.
