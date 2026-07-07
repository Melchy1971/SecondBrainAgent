"""Desktop / screenshot analysis: capture -> OCR -> text-classify -> ingest into Memory/RAG."""

from __future__ import annotations

import time
from typing import Any, Callable

from secondbrain.connectors.import_bridge import ConnectorImportBridge, ImportJobSink, InMemoryImportJobSink
from secondbrain.vision.ports import Image, OcrEngine, ScreenSource
from secondbrain.vision.classify import TextClassifier
from secondbrain.vision.ingest import ocr_to_item


class DesktopAnalyzer:
    def __init__(self, ocr: OcrEngine, *, screen: ScreenSource | None = None,
                 sink: ImportJobSink | None = None, text_classifier: TextClassifier | None = None) -> None:
        self.ocr = ocr
        self.screen = screen
        self.sink = sink or InMemoryImportJobSink()
        self.text_classifier = text_classifier

    def analyze_image(self, image: Image, *, source_uri: str | None = None, lang: str = "eng") -> dict[str, Any]:
        uri = source_uri or image.source_uri or "image://inline"
        result = self.ocr.recognize(image, lang=lang)
        labels = self.text_classifier.classify_text(result.text) if self.text_classifier else []
        item = ocr_to_item(result, source_uri=uri, labels=labels)
        bridge = ConnectorImportBridge(sink=self.sink)
        bridge.process_item(item)
        return {
            "source_uri": uri,
            "classification": [{"name": l.name, "score": l.score} for l in labels],
            "top_class": labels[0].name if labels else None,
            "ocr": {"chars": len(result.text), "blocks": len(result.blocks),
                    "mean_confidence": round(result.mean_confidence, 2)},
            "item": item.external_id,
            "import": bridge.snapshot(),
        }

    def analyze_screen(self, *, lang: str = "eng") -> dict[str, Any]:
        if self.screen is None:
            raise RuntimeError("no ScreenSource configured")
        return self.analyze_image(self.screen.capture(), source_uri="screenshot://desktop", lang=lang)

    def watch(self, interval_seconds: float, *, stop: Callable[[], bool],
              sleeper: Callable[[float], None] = time.sleep, max_cycles: int | None = None) -> list[dict]:
        runs: list[dict] = []
        while not stop():
            runs.append(self.analyze_screen())
            if max_cycles is not None and len(runs) >= max_cycles:
                break
            sleeper(interval_seconds)
        return runs
