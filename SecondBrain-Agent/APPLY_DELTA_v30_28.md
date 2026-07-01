# APPLY DELTA v30.28 — Native Action Audit & Approval Queue

## Inhalt

Dieses Delta erweitert v30.27 um persistentes Action-Audit und eine native Freigabe-Warteschlange.

## Dateien kopieren

Kopiere alle Dateien aus dem ZIP in dein Repository und überschreibe bestehende Dateien.

## Prüfen

```bash
pytest tests/test_v3028_native_action_audit_approval.py -q
python launcher.py native-status
python launcher.py native-action "Repariere Index" --dry-run
python launcher.py native-approval-list
python launcher.py native-action-audit
```

## Neue Runtime-Dateien

Diese Dateien werden zur Laufzeit erzeugt und gehören nicht ins Git:

```text
runtime/native/action_audit.jsonl
runtime/native/approval_queue.jsonl
```

## Erwartetes Verhalten

- Lesende Aktionen laufen direkt.
- Navigation läuft direkt.
- Schreibende Aktionen erzeugen einen Pending-Approval-Eintrag.
- Bestätigte Aktionen werden zusätzlich auditiert.
