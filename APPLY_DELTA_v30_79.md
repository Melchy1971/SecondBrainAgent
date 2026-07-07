# APPLY DELTA v30.79 — Google Workspace + Connector-Scaffold

## Neu
- `secondbrain/connectors/scaffold/` (10 Module) — wiederverwendbare Connector-Basis.
- `secondbrain/connectors/google/` (14 Module) — Gmail/Calendar/Drive/Contacts/Tasks.
- `secondbrain/connectors/microsoft/` — auf Scaffold umgestellt (Verhalten unverändert).
- `tests/connectors/{microsoft,google}/` — 52 Offline-Tests.
- `launcher.py` — Kommandos `google-login|google-sync|google-status|google-disconnect`.

## Validierung (grün in Sandbox)
```
python -m compileall SecondBrain-Agent/secondbrain/connectors/scaffold SecondBrain-Agent/secondbrain/connectors/google
pytest SecondBrain-Agent/tests/connectors -q      # 52 passed
```
Python 3.11+ für Launcher/Repo-Gesamtlauf (Repo nutzt datetime.UTC).

## Vor Live-Betrieb
1. Google-OAuth-Client anlegen + `.env` (siehe docs/releases/v30_79_google_workspace.md).
2. `google-login`, dann `google-sync` als Abnahme.
