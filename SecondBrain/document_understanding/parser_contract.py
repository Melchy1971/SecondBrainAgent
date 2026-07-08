"""P1.3.1 - Document parser contract and normalization boundary.

This module gives document ingestion a stable internal contract. Parsers return a
``ParsedDocument`` instead of leaking library-specific reader output into storage,
RAG indexing, connector imports, or UI code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class ParseStatus(str, Enum):
    """Stable parser states used by ingestion and release gates."""

    PARSED = "parsed"
    EMPTY = "empty"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    OCR_REQUIRED = "ocr_required"


@dataclass(frozen=True, slots=True)
class ParsedPage:
    """Text extracted from one logical page/section."""

    number: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_text(self) -> str:
        return normalize_text(self.text)


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Library-independent parsed document representation."""

    title: str
    text: str
    mime_type: str
    source_path: str | None = None
    status: ParseStatus = ParseStatus.PARSED
    pages: tuple[ParsedPage, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status == ParseStatus.PARSED

    @property
    def char_count(self) -> int:
        return len(self.text or "")

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def to_ingestion_payload(self) -> dict[str, Any]:
        """Return a storage-safe payload for the existing ingestion runtime."""

        return {
            "title": self.title,
            "text": self.text,
            "source_path": self.source_path or "manual",
            "mime_type": self.mime_type,
            "metadata": {
                "parse_status": self.status.value,
                "pages": self.page_count,
                "chars": self.char_count,
                **dict(self.metadata),
            },
            "errors": list(self.errors),
        }


@runtime_checkable
class DocumentParser(Protocol):
    """Parser interface implemented by file-type specific readers."""

    supported_extensions: set[str]

    def parse(self, path: str | Path) -> ParsedDocument:
        """Parse a document path into a normalized parsed document."""
        ...


def normalize_text(text: str | None) -> str:
    """Normalize extracted text without destroying paragraph boundaries.

    Rules:
    - convert CRLF/CR to LF
    - strip trailing whitespace per line
    - collapse runs of horizontal whitespace
    - collapse 3+ blank lines to 2
    - strip leading/trailing document whitespace
    """

    import re

    value = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    value = "\n".join(re.sub(r"[\t \f\v]+", " ", line).strip() for line in value.split("\n"))
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def build_parsed_document(
    *,
    title: str,
    text: str | None,
    mime_type: str,
    source_path: str | Path | None = None,
    pages: list[ParsedPage] | tuple[ParsedPage, ...] | None = None,
    metadata: dict[str, Any] | None = None,
    errors: list[str] | tuple[str, ...] | None = None,
    status: ParseStatus | None = None,
) -> ParsedDocument:
    """Create a normalized ``ParsedDocument`` with deterministic status handling."""

    normalized_pages = tuple(
        ParsedPage(number=page.number, text=normalize_text(page.text), metadata=dict(page.metadata))
        for page in (pages or ())
    )
    page_text = "\n\n".join(page.text for page in normalized_pages if page.text)
    normalized_text = normalize_text(text if text is not None else page_text)
    resolved_status = status or (ParseStatus.PARSED if normalized_text else ParseStatus.EMPTY)
    return ParsedDocument(
        title=title.strip() or "Untitled Document",
        text=normalized_text,
        mime_type=mime_type,
        source_path=str(source_path) if source_path is not None else None,
        status=resolved_status,
        pages=normalized_pages,
        metadata=dict(metadata or {}),
        errors=tuple(str(error) for error in (errors or ())),
    )
