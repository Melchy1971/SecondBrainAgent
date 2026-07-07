"""Vision orchestration: capture/decode -> OCR (+classify) -> ingest into Memory/RAG."""

from __future__ import annotations

from typing import Any

from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.vision.ports import Image, OcrEngine, ImageClassifier, ScreenSource
from secondbrain.vision.ingest import ocr_to_item


class VisionPipeline:
    def __init__(self, ocr: OcrEngine, *, sink: ImportJobSink | None = None,
                 classifier: ImageClassifier | None = None) -> None:
        self.ocr = ocr
        self.sink = sink or InMemoryImportJobSink()
        self.classifier = classifier

    def process_image(self, image: Image, *, source_uri: str | None = None, lang: str = "eng") -> dict[str, Any]:
        uri = source_uri or image.source_uri or "image://inline"
        result = self.ocr.recognize(image, lang=lang)
        labels = self.classifier.classify(image) if self.classifier else []
        item = ocr_to_item(result, source_uri=uri, labels=labels)
        bridge = ConnectorImportBridge(sink=self.sink)
        bridge.process_item(item)
        return {
            "source_uri": uri,
            "ocr": {"chars": len(result.text), "blocks": len(result.blocks),
                    "mean_confidence": round(result.mean_confidence, 2), "language": result.language},
            "labels": [{"name": l.name, "score": round(l.score, 3)} for l in labels],
            "item": item.external_id,
            "import": bridge.snapshot(),
        }

    def process_path(self, path: str, *, lang: str = "eng") -> dict[str, Any]:
        return self.process_image(Image.from_path(path), lang=lang)

    def process_screenshot(self, screen: ScreenSource, *, lang: str = "eng") -> dict[str, Any]:
        return self.process_image(screen.capture(), source_uri="screenshot://capture", lang=lang)
