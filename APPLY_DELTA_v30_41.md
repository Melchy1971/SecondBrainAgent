# APPLY DELTA v30.41 – Native Docking Layout

## Ziel
Phase 1 wird mit einem nativen Docking-/Layout-System fortgeführt. Die Anwendung erhält gespeicherte Arbeitslayouts für Standard, Entwicklung, Dokumente, Chat, Analyse und Vollbild.

## Enthaltene Dateien

```text
launcher.py
secondbrain/native/layout_center/__init__.py
secondbrain/native/layout_center/models.py
secondbrain/native/layout_center/service.py
secondbrain/native/layout_center/cli.py
secondbrain/native/layout_center/gui.py
secondbrain/native/ai_workspace/__init__.py
secondbrain/native/ai_workspace/models.py
secondbrain/native/ai_workspace/service.py
tests/test_v3041_native_docking_layout.py
RELEASE_NOTES_v30_41.md
```

## Anwenden

ZIP im Projektroot entpacken und vorhandene Dateien überschreiben.

```bash
python launcher.py layout-status
python launcher.py layout-list
python launcher.py layout-center-gui
pytest tests/test_v3041_native_docking_layout.py -q
```

## Neue Kommandos

```bash
python launcher.py layout-status
python launcher.py layout-list
python launcher.py layout-load default
python launcher.py layout-activate developer
python launcher.py layout-reset
python launcher.py layout-export default
python launcher.py layout-import mein_layout.json --activate
python launcher.py layout-history
python launcher.py layout-center-gui
```

## Runtime-Dateien

Werden erst zur Laufzeit erzeugt und sind nicht Bestandteil des ZIPs:

```text
runtime/native/layouts/default.json
runtime/native/layouts/developer.json
runtime/native/layouts/documents.json
runtime/native/layouts/chat.json
runtime/native/layouts/analysis.json
runtime/native/layouts/fullscreen.json
runtime/native/layouts/active_layout.json
runtime/native/layouts/layout_history.jsonl
```

## Akzeptanz

- Layout Defaults werden automatisch erzeugt.
- Aktives Layout ist persistiert.
- Layouts können geladen, aktiviert, exportiert, importiert und zurückgesetzt werden.
- AI Workspace Navigation enthält das Modul `Layout`.
- Keine Runtime-, Cache- oder Bytecode-Dateien im Delta.
