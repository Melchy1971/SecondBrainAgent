# APPLY DELTA v30.81 — Desktop-Analyse + Klassifikation

## Neu
- `secondbrain/vision/classify.py`, `desktop.py`, `engines/screen_mss.py`.
- `tests/vision/test_classify.py`, `test_desktop.py`, `test_mss_integration.py`.
- `launcher.py` — `desktop-analyze [--image <path>] [--lang]`.

## Validierung (Sandbox)
```
pytest SecondBrain-Agent/tests/vision -q         # 17 passed, 1 skipped (mss)
pytest SecondBrain-Agent/tests/connectors SecondBrain-Agent/tests/vision -q   # 69 passed, 1 skipped
```

## Live (deine GPU-Maschine)
`pip install -r requirements-vision.txt` (+ tesseract-Binary), dann `desktop-analyze`.
