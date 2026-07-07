# APPLY DELTA v30.80 — Vision/OCR

## Neu
- `secondbrain/vision/` — Ports, Fake-/Tesseract-Engines, Ingest, Pipeline.
- `tests/vision/` — 7 Unit-Tests (Fakes) + Tesseract-Integrationstest (importorskip).
- `requirements-vision.txt` — optionale Extras (offline, GPU-optional).
- `launcher.py` — Kommando `vision-ocr <path> [--lang]`.

## Validierung (Sandbox)
```
python -m compileall SecondBrain-Agent/secondbrain/vision
pytest SecondBrain-Agent/tests/vision -q     # 7 passed, 1 skipped (kein tesseract)
```

## Live (deine GPU-Maschine)
1. `pip install -r requirements-vision.txt` + System-`tesseract`.
2. `python launcher.py vision-ocr scan.png --lang deu` als Abnahme.
