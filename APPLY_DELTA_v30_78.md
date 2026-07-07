# APPLY DELTA v30.78 — M365 / Microsoft Graph

## Neu
- `SecondBrain-Agent/secondbrain/connectors/microsoft/` — Graph-Integration (19 Module).
- `SecondBrain-Agent/tests/connectors/microsoft/` — 33 Offline-Tests (FakeTransport).
- `launcher.py` — Kommandos `m365-login|m365-sync|m365-status|m365-disconnect` (+ `_m365_main`).

## Validierung (grün in Sandbox)
```
python -m compileall SecondBrain-Agent/secondbrain/connectors/microsoft
pytest SecondBrain-Agent/tests/connectors/microsoft -q     # 33 passed
```
Hinweis: Voller `pytest`-Repo-Lauf + `launcher.py m365-*` brauchen Python 3.11+ (Repo nutzt datetime.UTC).

## Vor Live-Betrieb
1. Azure-App registrieren + `.env` setzen (siehe docs/releases/v30_78_m365_graph.md).
2. `m365-login` auf deiner Maschine ausführen.
3. Abnahme: `m365-sync` mit fehlerfreiem Live-Lauf.
