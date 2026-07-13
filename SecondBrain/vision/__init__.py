"""Vision / OCR subsystem (v30.80), offline-first.

Three layers so the standard test suite stays green without models/hardware:
- ports:      pure Protocols + data models (stdlib-only, unit-testable with fakes)
- engines:    concrete adapters (Tesseract, screen/camera capture) - lazy imports, integration-only
- pipeline:   orchestration + ingest into Memory/RAG via the existing ConnectorImportBridge
"""

from secondbrain.vision.ports import (
    Image, OcrBlock, OcrResult, OcrEngine, Label, ImageClassifier, Box, ObjectDetector,
    ScreenSource, CameraSource,
)
from secondbrain.vision.ingest import ocr_to_item, result_to_items
from secondbrain.vision.pipeline import VisionPipeline
from secondbrain.vision.classify import TextClassifier, HeuristicTextClassifier
from secondbrain.vision.desktop import DesktopAnalyzer
from secondbrain.vision.diagram import (
    DiagramNode, DiagramEdge, DiagramGraph, DiagramAnalyzer,
    build_diagram, KnowledgeGraphSink, InMemoryKnowledgeGraph,
)

__all__ = [
    "Image", "OcrBlock", "OcrResult", "OcrEngine", "Label", "ImageClassifier",
    "Box", "ObjectDetector", "ScreenSource", "CameraSource",
    "ocr_to_item", "result_to_items", "VisionPipeline",
    "TextClassifier", "HeuristicTextClassifier", "DesktopAnalyzer",
    "DiagramNode", "DiagramEdge", "DiagramGraph", "DiagramAnalyzer",
    "build_diagram", "KnowledgeGraphSink", "InMemoryKnowledgeGraph",
]
