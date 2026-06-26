# APPLY DELTA v30.24 – GUI Memory Center Runtime Truth

## Ziel
Memory-Ansicht von statischer Vault-Liste zu Runtime-Truth-Oberfläche erweitern.

## Enthalten
- `secondbrain/gui/memory_center_runtime.py`
- `secondbrain/jarvis_hud_server.py`
- `launcher.py`
- `web/jarvis_hud/index.html`
- `tests/test_v3024_memory_center_runtime.py`
- `docs/09_MASTERPLAN_STATUS.json`

## Anwendung
Dateien ins Repo kopieren und bestehende Dateien überschreiben.

## Prüfung
```bash
python launcher.py memory-center-status
pytest tests/test_v3024_memory_center_runtime.py -q
pytest --collect-only -q
```

## Erwartung
- Memory Center zeigt Vault-, SQLite-, Semantic- und Episodic-Memory getrennt.
- Governance zeigt Privacy Mode, Secret Encryption, Data Classification.
- Unverschlüsselte SQLite-Memories blockieren den Status.
- Lineage-/Tag-Lücken werden sichtbar.
