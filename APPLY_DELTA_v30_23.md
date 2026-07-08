# APPLY DELTA v30.23 — Document Center Runtime Truth

## Inhalt

- `secondbrain/gui/document_center_runtime.py`
- `secondbrain/jarvis_hud_server.py`
- `web/jarvis_hud/index.html`
- `launcher.py`
- `tests/test_v3023_document_center_runtime.py`
- `docs/09_MASTERPLAN_STATUS.json`

## Neue Befehle

```bash
python launcher.py document-center-status
```

## Neue API

```text
GET /api/document-center/status
```

## GUI-Wirkung

Documents wurde zu Document Center erweitert. Sichtbar sind jetzt Index-Dokumente, Chunks, Vectors, Pending Imports, OCR-Status, Gate-Status, Parser-/MIME-Verteilung und letzte indexierte Dokumente.

## Validierung

```bash
pytest -q tests/test_v3023_document_center_runtime.py
```

Erwartung: `4 passed`.
