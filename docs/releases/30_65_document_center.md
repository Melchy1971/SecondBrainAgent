# v30.65 — Document-Center-Erweiterung

**Keine bestehenden Funktionen veraendert.** Alles neu in `secondbrain/documents/` (Logik) + eine
additive GUI-Datei. Das bestehende Document-Center (`gui/document_center_runtime.py`,
`desktop/documents/*`, `storage/repositories/document_repository.py`, `importing/*`) bleibt unangetastet.

## Neu (Logik, voll getestet)
- `preview.py` — Preview-Resolver (PDF/Office/Markdown/Code/Bild/Video/Audio/Text), Markdown->HTML,
  Syntax-Highlight-Tokenizer (nutzt pygments falls installiert, sonst deterministischer Fallback).
- `upload_queue.py` — **Mehrfachimport** + **Upload-Queue** mit Progress/Status.
- `import_history.py` — persistente **Import-History**.
- `tags.py` — **Tags** je Dokument (Filter, Persistenz).
- `versioning.py` — **Versionierung** (content-hash, dedupliziert, geordnet).
- `compare.py` — **Dokumentenvergleich** (unified diff + Similarity).
- `ocr_status.py` — **OCR-Status** je Dokument (angebunden an das vision-OCR-Subsystem v30.80).

## GUI (ehrlich deklariert)
`secondbrain/gui/document_center_pro.py` — Tkinter-Oberflaeche mit PDF/Office/Markdown/Bild/Video/Audio-
Preview, Syntax-Highlighting, **Drag&Drop** (tkdnd), Upload-Queue, Versions-/Diff-Ansicht.
**Wichtig:** Das ist Windows/Desktop-GUI-Code. Er wurde in der Build-Sandbox **nicht ausgefuehrt oder
abgenommen** (kein Display); `tkinter` wird lazy importiert, damit der Import headless nie bricht. Die
gesamte Logik dahinter (`secondbrain/documents/*`) ist unit-getestet. Rendering/Abnahme laeuft auf deiner Maschine.

## Launcher
```
python launcher.py doc-preview report.md
python launcher.py doc-diff v1.txt --against v2.txt
```

## Tests
`tests/documents/` (19 passed): Preview-Resolver (9 Typen), Markdown (Headings/Listen/Inline/Escape),
Highlighting (Keyword/String/Comment/Number), Tags (add/remove/find/persist), Versionierung (dedup/order),
Vergleich (added/removed/similarity), Upload-Queue-Lifecycle, Import-History-Persistenz, OCR-Status.

## Grenzen
Echte Preview-Rendering (PDF/Office/Video/Audio-Widgets), Drag&Drop und Player sind nur auf der
Windows-Maschine mit Display + optionalen Paketen (tkdnd/tkinterdnd2, ggf. Poppler/LibreOffice fuer
PDF/Office-Rasterung) validierbar. Office/PDF-Preview hier = Renderer-Auswahl + Contract, nicht die Rasterung.
