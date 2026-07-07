# v30.82 — Objekterkennung + Diagramme (offline, GPU)

Baut auf den Vision-Ports (v30.80/81). Vorgabe offline-only -> **kein Cloud-VLM**. Stattdessen
zwei ehrlich getrennte Teile.

## Neu
- `vision/engines/onnx_detector.py`: `OnnxObjectDetector` — echte Objekterkennung via ONNX Runtime
  (GPU: CUDAExecutionProvider), YOLOv8-artige Nachverarbeitung. Lazy-Import von onnxruntime/numpy/pillow,
  **Integration-only** (braucht Modelldatei + Deps).
- `vision/diagram.py`: `build_diagram(boxes, ocr) -> DiagramGraph` — **deterministische, offline**
  Strukturextraktion: Detektionen (Knoten/Kanten-Klassen) + OCR-Textzuordnung per Geometrie ->
  Knoten mit Labels + gerichtete Kanten. Plus `DiagramAnalyzer` (detect -> OCR -> Graph -> Ingest)
  und `KnowledgeGraphSink` (+ InMemory-Impl) für die Knowledge-Graph-Anbindung.

## Warum kein VLM
Ein lokales VLM (moondream/llava) wäre schwer und ohne GPU-Modell nicht grün testbar; Cloud ist per
Offline-Vorgabe ausgeschlossen. Die geometrie+OCR-Extraktion ist deterministisch, offline und liefert
für Flow-/Block-Diagramme einen sauberen Graphen — testbar ohne Modell.

## Testbarkeit
- Grün: `build_diagram` (Knoten/Kanten/Textzuordnung, keine Self-Edges) + `DiagramAnalyzer` mit Fakes,
  inkl. Knowledge-Graph- und Memory-Ingest.
- Übersprungen ohne Deps: mss-Capture. Der ONNX-Test läuft, wenn onnxruntime vorhanden ist
  (prüft Konstruktor-Fehler bei fehlendem Modell).

## Launcher (Python 3.11+, mit Deps + Modell)
```
python launcher.py diagram-analyze --image flow.png --model yolo-diagram.onnx --labels node,arrow --lang deu
```
Fehlende Engine/Deps -> `engine_unavailable`, kein Crash.

## Anbindung
DiagramGraph -> `KnowledgeGraphSink` (Knoten/Kanten) und als `ConnectorItem` -> `ConnectorImportBridge`
(Memory/RAG). Reale KG-Anbindung ist ein dünner Adapter auf den vorhandenen knowledge_graph-Stack.
