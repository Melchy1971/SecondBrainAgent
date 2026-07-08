"""Vision ports: stdlib-only Protocols and data models. Fully unit-testable."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Image:
    """Opaque image payload passed across the vision boundary."""
    data: bytes
    mime_type: str = "image/png"
    source_uri: str | None = None

    @classmethod
    def from_path(cls, path: str | Path) -> "Image":
        p = Path(path)
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif", "bmp": "image/bmp", "tiff": "image/tiff"}.get(p.suffix.lstrip(".").lower(), "application/octet-stream")
        return cls(data=p.read_bytes(), mime_type=mime, source_uri=p.as_uri())


@dataclass(frozen=True)
class OcrBlock:
    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None   # x, y, w, h


@dataclass(frozen=True)
class OcrResult:
    text: str
    blocks: list[OcrBlock] = field(default_factory=list)
    language: str = "eng"
    mean_confidence: float = 0.0

    @classmethod
    def from_blocks(cls, blocks: list[OcrBlock], *, language: str = "eng") -> "OcrResult":
        text = "\n".join(b.text for b in blocks if b.text.strip())
        conf = sum(b.confidence for b in blocks) / len(blocks) if blocks else 0.0
        return cls(text=text, blocks=list(blocks), language=language, mean_confidence=conf)


@runtime_checkable
class OcrEngine(Protocol):
    name: str
    def recognize(self, image: Image, *, lang: str = "eng") -> OcrResult: ...


@dataclass(frozen=True)
class Label:
    name: str
    score: float


@runtime_checkable
class ImageClassifier(Protocol):
    def classify(self, image: Image) -> list[Label]: ...


@dataclass(frozen=True)
class Box:
    label: str
    score: float
    xyxy: tuple[int, int, int, int]


@runtime_checkable
class ObjectDetector(Protocol):
    def detect(self, image: Image) -> list[Box]: ...


@runtime_checkable
class ScreenSource(Protocol):
    def capture(self) -> Image: ...


@runtime_checkable
class CameraSource(Protocol):
    def frame(self) -> Image: ...
