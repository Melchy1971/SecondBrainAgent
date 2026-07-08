"""Safe document preview models for the desktop document center."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .models import DesktopDocument, DocumentStatus


class PreviewStatus(str, Enum):
    READY = "READY"
    EMPTY = "EMPTY"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    ARCHIVED = "ARCHIVED"


TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "text/csv",
    "application/xml",
    "text/xml",
}

TEXT_EXTENSIONS = (".txt", ".md", ".markdown", ".json", ".csv", ".xml", ".log")


@dataclass(frozen=True)
class DocumentPreviewViewModel:
    """User-facing preview payload.

    The preview is intentionally bounded. It never exposes internal document IDs
    and keeps raw content out of metadata. The GUI can render this object without
    having to know parser internals.
    """

    title: str
    status: PreviewStatus
    content: str = ""
    message: str = ""
    content_type: str = "text"
    truncated: bool = False
    line_count: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def can_render(self) -> bool:
        return self.status == PreviewStatus.READY and bool(self.content)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _detect_content_type(document: DesktopDocument) -> str:
    metadata = document.metadata or {}
    mime_type = str(metadata.get("mime_type") or metadata.get("content_type") or "").lower().strip()
    filename = str(metadata.get("filename") or document.title or "").lower().strip()
    if mime_type in TEXT_MIME_TYPES or filename.endswith(TEXT_EXTENSIONS):
        return "text"
    if mime_type == "application/pdf" or filename.endswith(".pdf"):
        return "pdf"
    if mime_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return "image"
    return "unknown"


def _safe_preview_metadata(document: DesktopDocument) -> dict[str, str]:
    metadata = document.metadata or {}
    allowed = {}
    for key in ("filename", "mime_type", "content_type", "size_bytes", "page_count"):
        if key in metadata and metadata[key] not in (None, ""):
            allowed[key] = str(metadata[key])
    return allowed


def build_document_preview(
    document: DesktopDocument,
    *,
    max_chars: int = 2000,
    max_lines: int = 80,
) -> DocumentPreviewViewModel:
    """Build a bounded, safe preview for a desktop document.

    Source priority:
    1. metadata["preview_text"]
    2. metadata["text"]
    3. metadata["content"]

    Unsupported or failed documents return explicit status objects instead of
    raising presentation errors.
    """

    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    if max_lines < 1:
        raise ValueError("max_lines must be >= 1")

    if document.status == DocumentStatus.ARCHIVED:
        return DocumentPreviewViewModel(
            title=document.title,
            status=PreviewStatus.ARCHIVED,
            message="Dokument ist archiviert.",
            content_type=_detect_content_type(document),
            metadata=_safe_preview_metadata(document),
        )
    if document.status == DocumentStatus.FAILED:
        return DocumentPreviewViewModel(
            title=document.title,
            status=PreviewStatus.FAILED,
            message=str(document.metadata.get("error") or "Vorschau nicht verfügbar."),
            content_type=_detect_content_type(document),
            metadata=_safe_preview_metadata(document),
        )

    content_type = _detect_content_type(document)
    if content_type not in {"text", "pdf"}:
        return DocumentPreviewViewModel(
            title=document.title,
            status=PreviewStatus.UNSUPPORTED,
            message="Für diesen Dateityp ist keine Textvorschau verfügbar.",
            content_type=content_type,
            metadata=_safe_preview_metadata(document),
        )

    raw = document.metadata.get("preview_text") or document.metadata.get("text") or document.metadata.get("content")
    text = _normalize_text(raw)
    if not text:
        return DocumentPreviewViewModel(
            title=document.title,
            status=PreviewStatus.EMPTY,
            message="Keine Vorschauinhalte vorhanden.",
            content_type=content_type,
            metadata=_safe_preview_metadata(document),
        )

    lines = text.split("\n")
    truncated = False
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
        truncated = True

    return DocumentPreviewViewModel(
        title=document.title,
        status=PreviewStatus.READY,
        content=text,
        content_type=content_type,
        truncated=truncated,
        line_count=len(text.split("\n")) if text else 0,
        metadata=_safe_preview_metadata(document),
    )
