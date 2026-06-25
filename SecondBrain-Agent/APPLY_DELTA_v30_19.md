# Apply Delta v30.19 - P1 GUI Surface Update

## Inhalt
Dieses Delta aktualisiert die bestehenden GUI-/Desktop-Oberflächen für die P0/P1-Funktionen aus v30.6 bis v30.18.

## Dateien kopieren
ZIP im Projektroot entpacken und vorhandene Dateien überschreiben.

## Validierung
```bash
python -m py_compile secondbrain/desktop/app.py secondbrain/gui/p1_control_panel.py secondbrain/gui/settings_center.py secondbrain/gui/production_dashboard.py secondbrain/gui/rag_explorer.py
pytest -q tests/test_v3019_gui_p1_surface.py tests/desktop/test_app.py
pytest --collect-only -q
```

## Neue Views
- `rag-import`
- `rag-index`
- `p1-control`
- `production`
- `settings-p1`

## Neue GUI-Kommandos
- `open.rag-import`
- `open.rag-index`
- `open.p1-control`
- `open.production`
- `open.settings-p1`
- `action.p1.*` Runtime-Action-Descriptors
