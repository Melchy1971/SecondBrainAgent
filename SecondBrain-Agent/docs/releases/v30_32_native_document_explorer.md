# v30.32 Native Document Explorer Center

## Ziel
Dokumente werden in der nativen Desktop-Anwendung als eigener Arbeitsbereich sichtbar. Der Web-HUD bleibt sekundär.

## Neu
- `secondbrain.native.document_explorer.DocumentExplorer`
- `secondbrain.native.document_explorer_gui`
- Launcher-Kommandos:
  - `document-explorer-status`
  - `document-explorer-list`
  - `document-explorer-search`
  - `document-explorer-info`
  - `document-explorer-preview`
  - `document-explorer-tag`
  - `document-explorer-import`
  - `document-explorer-gui`

## Runtime-Dateien
- `runtime/native/document_explorer_meta.json`
- `runtime/native/activity_log.jsonl`

## Grenzen
- PDF-/Bildvorschau wird als externer Preview-Hinweis gemeldet.
- OCR wird markiert, aber noch nicht ausgeführt.
- Versionierung ist vorbereitet, aber noch nicht vollständig umgesetzt.
