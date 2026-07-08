"""Deterministic fake engines for unit tests / dry runs (no models)."""

from __future__ import annotations

from secondbrain.vision.ports import (
    Image, OcrBlock, OcrResult, Label, Box,
)


class FakeOcrEngine:
    name = "fake-ocr"

    def __init__(self, text: str = "Hello World", confidence: float = 0.95) -> None:
        self._text = text
        self._conf = confidence

    def recognize(self, image: Image, *, lang: str = "eng") -> OcrResult:
        blocks = [OcrBlock(text=line, confidence=self._conf, bbox=(0, i * 10, 100, 10))
                  for i, line in enumerate(self._text.splitlines() or [self._text])]
        return OcrResult.from_blocks(blocks, language=lang)


class FakeClassifier:
    def __init__(self, labels=None) -> None:
        self._labels = labels or [Label("document", 0.9)]

    def classify(self, image: Image) -> list[Label]:
        return list(self._labels)


class FakeObjectDetector:
    def __init__(self, boxes=None) -> None:
        self._boxes = boxes or [Box("text", 0.8, (0, 0, 100, 20))]

    def detect(self, image: Image) -> list[Box]:
        return list(self._boxes)


class FakeScreenSource:
    def __init__(self, image: Image | None = None) -> None:
        self._image = image or Image(data=b"\x89PNG-fake", mime_type="image/png", source_uri="screenshot://fake")

    def capture(self) -> Image:
        return self._image
