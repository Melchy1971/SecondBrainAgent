# v30.80 — Vision/OCR-Subsystem (offline, GPU-optional)

## Entscheidungen (von dir)
Offline-Pflicht, GPU vorhanden, ML-Deps als optionale Extras. Umgesetzt: keine Cloud-Calls,
schwere Pakete nur in `requirements-vision.txt`, Kern bleibt stdlib-only.

## Drei Schichten (damit Standard-pytest ohne Modelle grün bleibt)
- **ports** (`secondbrain/vision/ports.py`): Protocols + Datenmodelle (Image, OcrResult/OcrBlock,
  OcrEngine, ImageClassifier, ObjectDetector, ScreenSource, CameraSource). Stdlib-only, unit-testbar.
- **engines** (`secondbrain/vision/engines/`): `fake.py` (deterministisch, für Tests) und
  `tesseract_ocr.py` (offline; **lazy** pytesseract/pillow-Import, Integration-only).
- **pipeline** (`secondbrain/vision/pipeline.py`): Capture/Decode -> OCR (+Klassifikation) ->
  Ingest als `ConnectorItem` über `ConnectorImportBridge` in Memory/RAG. Kein zweiter Ingestion-Weg.

## Testbarkeit / Abnahme
- 7 Unit-Tests grün mit Fakes (Ports, Ingest, Pipeline, Idempotenz über content_hash).
- Tesseract-Integrationstest nutzt `pytest.importorskip` -> ohne installierte Engine übersprungen,
  bricht den Lauf **nicht**. Echte OCR-Abnahme (Golden-Set, CER-Schwelle) läuft auf deiner GPU-Maschine.

## Launcher (Python 3.11+, mit optionalen Deps)
```
python launcher.py vision-ocr /pfad/scan.png --lang deu
```
Ohne installierte Engine: sauberer `engine_unavailable`-Hinweis auf requirements-vision.txt, kein Crash.

## Scope-Grenze (bewusst)
v30.80 liefert OCR + Ingest + Orchestrierung + Ports für Klassifikation/Objekterkennung/Capture.
Reale Screenshot-/Kamera-Capture (mss/opencv), Klassifikator und GPU-Objekterkennung (onnxruntime-gpu/
ultralytics) sind als Ports vorhanden und werden in v30.81/v30.82 mit echten Adaptern gefüllt
(siehe OUTPUTS/v30_80_ml_subsystems/ML_ARCHITECTURE_PLAN.md).
