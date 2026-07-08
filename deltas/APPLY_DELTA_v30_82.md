# APPLY DELTA v30.82 — Objekterkennung + Diagramme

## Neu
- `secondbrain/vision/diagram.py`, `secondbrain/vision/engines/onnx_detector.py`.
- `tests/vision/test_diagram.py`, `test_onnx_integration.py`.
- `launcher.py` — `diagram-analyze --image <path> --model <onnx> [--labels ...]`.

## Validierung (Sandbox)
```
pytest SecondBrain-Agent/tests/vision -q          # 21 passed, 1 skipped (mss)
pytest SecondBrain-Agent/tests/connectors SecondBrain-Agent/tests/vision -q   # 73 passed, 1 skipped
```

## Live (deine GPU-Maschine)
`pip install onnxruntime-gpu numpy pillow` + ONNX-Diagrammmodell, dann `diagram-analyze`.
