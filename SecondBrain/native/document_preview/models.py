"""v30.47 - UI-freie Modelle des Document Preview Centers.

Kein zweiter Dokumentkatalog: die Modelle arbeiten auf den Ergebnissen des
bestehenden DocumentExplorer und der document_understanding-Parser. Alles hier
ist Tk-frei und laeuft headless in Tests.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

SUPPORTED_PREVIEW_EXTENSIONS = (
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".md",
    ".markdown",
    ".json",
)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


class ZoomModel:
    """Deterministische Zoom-Stufen fuer Canvas- und Text-Vorschau."""

    MIN = 0.25
    MAX = 4.0
    STEP = 0.25
    DEFAULT = 1.0

    @classmethod
    def clamp(cls, value: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return cls.DEFAULT
        return max(cls.MIN, min(cls.MAX, round(numeric / cls.STEP) * cls.STEP))

    @classmethod
    def zoom_in(cls, value: float) -> float:
        return cls.clamp(cls.clamp(value) + cls.STEP)

    @classmethod
    def zoom_out(cls, value: float) -> float:
        return cls.clamp(cls.clamp(value) - cls.STEP)

    @classmethod
    def levels(cls) -> list[float]:
        steps = int(round((cls.MAX - cls.MIN) / cls.STEP)) + 1
        return [round(cls.MIN + index * cls.STEP, 2) for index in range(steps)]


@dataclass(frozen=True)
class PreviewAnnotation:
    """Eine Annotation auf einem Dokument (optional mit Seiten- und Regionsbezug)."""

    annotation_id: str
    document_id: str
    text: str
    page: int | None = None
    region: tuple[float, float, float, float] | None = None
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["region"] = list(self.region) if self.region is not None else None
        return data

    @staticmethod
    def create(document_id: str, text: str, *, page: int | None = None,
               region: Iterable[float] | None = None) -> "PreviewAnnotation":
        clean_region: tuple[float, float, float, float] | None = None
        if region is not None:
            values = [float(item) for item in region]
            if len(values) != 4:
                raise ValueError("annotation_region_requires_four_values")
            clean_region = (values[0], values[1], values[2], values[3])
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("annotation_text_required")
        return PreviewAnnotation(
            annotation_id=f"ann_{uuid.uuid4().hex[:12]}",
            document_id=document_id,
            text=clean_text,
            page=int(page) if page is not None else None,
            region=clean_region,
            created_at=time.time(),
        )

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PreviewAnnotation":
        region = data.get("region")
        return PreviewAnnotation(
            annotation_id=str(data.get("annotation_id", "")),
            document_id=str(data.get("document_id", "")),
            text=str(data.get("text", "")),
            page=int(data["page"]) if data.get("page") is not None else None,
            region=tuple(float(v) for v in region) if region else None,  # type: ignore[arg-type]
            created_at=float(data.get("created_at", 0.0)),
        )


@dataclass(frozen=True)
class PreviewVersion:
    """Ein inhaltsbasierter Versionsstand (Hash-Snapshot) eines Dokuments."""

    version_id: str
    document_id: str
    source_path: str
    snapshot_path: str
    size_bytes: int
    content_hash: str
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PreviewVersion":
        return PreviewVersion(
            version_id=str(data.get("version_id", "")),
            document_id=str(data.get("document_id", "")),
            source_path=str(data.get("source_path", "")),
            snapshot_path=str(data.get("snapshot_path", "")),
            size_bytes=int(data.get("size_bytes", 0)),
            content_hash=str(data.get("content_hash", "")),
            created_at=float(data.get("created_at", 0.0)),
        )


class PreviewSearchModel:
    """Volltextsuche ueber extrahierten Parser-Text (seiten- und zeilengenau)."""

    @staticmethod
    def hits(pages: Iterable[dict[str, Any]], query: str, *, limit: int = 200,
             context_chars: int = 60) -> list[dict[str, Any]]:
        query_norm = (query or "").strip().lower()
        if not query_norm:
            return []
        results: list[dict[str, Any]] = []
        for page in pages:
            number = int(page.get("number", 1))
            text = str(page.get("text", ""))
            for line_index, line in enumerate(text.splitlines(), start=1):
                lowered = line.lower()
                start = 0
                while True:
                    found = lowered.find(query_norm, start)
                    if found < 0:
                        break
                    left = max(0, found - context_chars)
                    right = min(len(line), found + len(query_norm) + context_chars)
                    results.append({
                        "page": number,
                        "line": line_index,
                        "column": found + 1,
                        "context": line[left:right].strip(),
                    })
                    if len(results) >= limit:
                        return results
                    start = found + len(query_norm)
        return results

    @staticmethod
    def pages_from_parsed(parsed: dict[str, Any]) -> list[dict[str, Any]]:
        pages = parsed.get("pages") or []
        if pages:
            return [{"number": row.get("number", idx + 1), "text": row.get("text", "")}
                    for idx, row in enumerate(pages)]
        return [{"number": 1, "text": str(parsed.get("text", ""))}]


class OcrOverlayModel:
    """Overlay-Modell: OCR-Status plus optionale Wort-Boxen fuer die Canvas."""

    @staticmethod
    def engine_available() -> bool:
        try:
            import pytesseract  # type: ignore[import-not-found]  # noqa: F401
            from PIL import Image  # type: ignore[import-not-found]  # noqa: F401
        except Exception:  # noqa: BLE001 - optional dependency boundary
            return False
        return True

    @staticmethod
    def normalize_items(raw: dict[str, Any]) -> list[dict[str, Any]]:
        """pytesseract.image_to_data(dict) -> stabile Overlay-Items."""
        items: list[dict[str, Any]] = []
        texts = raw.get("text") or []
        for index, word in enumerate(texts):
            word_clean = str(word).strip()
            if not word_clean:
                continue
            try:
                confidence = float(raw.get("conf", [])[index])
            except (IndexError, TypeError, ValueError):
                confidence = -1.0
            try:
                left = int(raw.get("left", [])[index])
                top = int(raw.get("top", [])[index])
                width = int(raw.get("width", [])[index])
                height = int(raw.get("height", [])[index])
            except (IndexError, TypeError, ValueError):
                continue
            items.append({
                "text": word_clean,
                "confidence": confidence,
                "bbox": [left, top, left + width, top + height],
            })
        return items


@dataclass
class PreviewState:
    """UI-unabhaengiger Zustand der Vorschau (fuer GUI und Tests)."""

    document_id: str | None = None
    path: str | None = None
    extension: str | None = None
    page: int = 1
    page_count: int = 1
    zoom: float = ZoomModel.DEFAULT
    overlay_enabled: bool = False
    search_query: str = ""
    search_hits: list[dict[str, Any]] = field(default_factory=list)

    def set_zoom(self, value: float) -> float:
        self.zoom = ZoomModel.clamp(value)
        return self.zoom

    def set_page(self, page: int) -> int:
        self.page = max(1, min(int(page), max(1, self.page_count)))
        return self.page

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "path": self.path,
            "extension": self.extension,
            "page": self.page,
            "page_count": self.page_count,
            "zoom": self.zoom,
            "overlay_enabled": self.overlay_enabled,
            "search_query": self.search_query,
            "search_hits": list(self.search_hits),
        }
