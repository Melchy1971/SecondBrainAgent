# v30.28 Native Action Audit & Approval Queue

## Ziel
Native Desktop und deutsche Sprachsteuerung dürfen schreibende Aktionen nicht nur blockieren, sondern müssen sie nachvollziehbar protokollieren und als Freigabeobjekt sichtbar machen.

## Änderungen

- Action Audit für jede native/Voice-Aktion.
- JSONL Audit-Datei: `runtime/native/action_audit.jsonl`.
- Freigabe-Warteschlange für schreibende Aktionen.
- JSONL Queue-Datei: `runtime/native/approval_queue.jsonl`.
- Neue Launcher-Kommandos:
  - `native-action-audit`
  - `native-approval-list`
  - `native-approval-run <approval_id>`
  - `native-approval-reject <approval_id>`
- Native GUI bekommt Tab `Audit / Freigaben`.
- ViewModel aktualisiert auf `secondbrain.native.view_model.v30_28`.

## Risikoabbau

Vorher:
- Bestätigung war nur ein UI-Zustand.
- Abgelehnte oder wartende Aktionen waren nicht persistiert.
- Ausführungshistorie war nicht revisionsfähig.

Nachher:
- Jede Aktion erzeugt Audit-Evidenz.
- Mutierende Befehle erzeugen Pending Approval.
- Freigaben können getrennt geprüft, ausgeführt oder abgelehnt werden.

## Validierung

```bash
pytest tests/test_v3028_native_action_audit_approval.py -q
python launcher.py native-action "Repariere Index" --dry-run
python launcher.py native-approval-list
python launcher.py native-action-audit
```
