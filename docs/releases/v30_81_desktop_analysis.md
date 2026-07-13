# v30.81 — Screenshot/Desktop-Analyse + Klassifizierung

Baut auf den Vision-Ports (v30.80). Fokus: Bildschirm/Screenshot erfassen, Text erkennen,
**klassifizieren**, in Memory/RAG ablegen.

## Neu
- `vision/classify.py`: `TextClassifier`-Port + `HeuristicTextClassifier` — **regelbasiert,
  offline, deterministisch** (kein Modell). Klassen: invoice, email, code, chat, calendar,
  generic, empty. Damit ist „Klassifizierung" echt und grün testbar, kein Stub.
- `vision/desktop.py`: `DesktopAnalyzer` — capture -> OCR -> Textklassifikation -> Ingest als
  `ConnectorItem` über `ConnectorImportBridge`. `watch(interval, stop, max_cycles)` für periodische Analyse.
- `vision/engines/screen_mss.py`: `MssScreenSource` — Bildschirm-Capture via `mss` (lazy, offline,
  Integration-only).

## Ehrliche Trennung testbar / hardwareabhängig
- Grün im Standardlauf: Klassifikation + DesktopAnalyzer mit Fake-OCR/Fake-Screen (17 passed).
- Übersprungen ohne optionale Dep: `mss`-Integrationstest (`importorskip`).
- Echte Screenshot-OCR-Abnahme (Tesseract + mss) läuft auf deiner Maschine.

## Launcher (Python 3.11+, mit optionalen Deps)
```
python launcher.py desktop-analyze                 # Live-Screen (mss + tesseract)
python launcher.py desktop-analyze --image scan.png --lang deu   # Datei, ohne mss
```
Fehlende Engine -> `engine_unavailable`-Hinweis, kein Crash.

## Grenze
Bild-basierte Klassifikation/Objekterkennung (GPU, onnxruntime/ultralytics) bleibt v30.82.
Hier klassifiziert der erkannte **Text**, nicht das Bild — bewusst, weil offline + deterministisch.
