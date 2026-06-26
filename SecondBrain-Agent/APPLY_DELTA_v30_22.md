# APPLY DELTA v30.22 — GUI Runtime Truth Update

## Inhalt

Dieses Delta aktualisiert die Jarvis-HUD-GUI auf den aktuellen Entwicklungsstand v30.22.

Geänderte/neue Dateien:

- `SecondBrain-Agent/secondbrain/jarvis_hud_server.py`
- `SecondBrain-Agent/web/jarvis_hud/index.html`
- `SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json`
- `SecondBrain-Agent/RELEASE_NOTES.md`
- `SecondBrain-Agent/tests/test_v3022_gui_runtime_truth.py`

## Umsetzung

- Neuer Endpoint: `GET /api/runtime-truth`
- HUD zeigt Runtime-Truth für:
  - Datenbank/Store
  - pgvector
  - Embedding Provider/Modell/Dimension
  - Index Identity `provider:model:dimension`
  - Production Gate
  - Golden Quality
  - Migration SQLite→PostgreSQL
  - Vector Audit
  - Secret Vault
  - Connector Runtime
- Settings-Modal erweitert um P1-Runtime-/ENV-/Security-Felder.
- Statische GUI-Demo-Werte bleiben Fallback, werden aber durch Runtime-Fakten überschrieben.

## Anwendung

Dateien aus dem ZIP in das Repo kopieren und vorhandene Dateien überschreiben.

Danach ausführen:

```bash
cd SecondBrain-Agent
python -m py_compile secondbrain/jarvis_hud_server.py
pytest -q tests/test_v3022_gui_runtime_truth.py
python launcher.py gui
```

## Validierung im Sandbox-Lauf

```text
pytest -q tests/test_v3022_gui_runtime_truth.py
3 PASS
```

## Nicht erledigt

- Volltest ohne Sandbox-Timeout.
- Live-VPS PostgreSQL/pgvector-Test.
- Native EXE/MSI-Installer.
- Produktive Secret-Vault-Implementierung.
- Produktive OAuth-Connector-Runtime.
