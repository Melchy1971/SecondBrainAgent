"""P1.3.1 - Default document parsers for the ingestion boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .parser_contract import ParsedDocument, ParsedPage, ParseStatus, build_parsed_document


MIME_BY_EXTENSION = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".eml": "message/rfc822",
    ".pdf": "application/pdf",
}


class PlainTextParser:
    """Parser for UTF-8 compatible text-like documents."""

    supported_extensions = {".txt", ".md", ".csv", ".json", ".eml"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="ignore")
        return build_parsed_document(
            title=p.name,
            text=text,
            mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "text/plain"),
            source_path=p,
            metadata={"parser": "plain_text"},
        )


class PdfTextParser:
    """PDF parser with optional PyMuPDF/pypdf support and explicit failure state."""

    supported_extensions = {".pdf"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = Path(path)
        errors: list[str] = []
        pages: list[ParsedPage] = []

        try:
            import fitz  # type: ignore

            with fitz.open(p) as doc:
                for index, page in enumerate(doc, start=1):
                    pages.append(ParsedPage(number=index, text=page.get_text("text") or ""))
            return build_parsed_document(
                title=p.name,
                text=None,
                mime_type="application/pdf",
                source_path=p,
                pages=pages,
                metadata={"parser": "pymupdf"},
            )
        except Exception as exc:  # noqa: BLE001 - parser fallback boundary
            errors.append(f"pymupdf:{exc}")

        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(p))
            for index, page in enumerate(reader.pages, start=1):
                pages.append(ParsedPage(number=index, text=page.extract_text() or ""))
            return build_parsed_document(
                title=p.name,
                text=None,
                mime_type="application/pdf",
                source_path=p,
                pages=pages,
                metadata={"parser": "pypdf"},
                errors=errors,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pypdf:{exc}")

        return build_parsed_document(
            title=p.name,
            text="",
            mime_type="application/pdf",
            source_path=p,
            metadata={"parser": "pdf_text"},
            errors=errors,
            status=ParseStatus.FAILED,
        )


class ParserRegistry:
    """Extension based parser registry with deterministic unsupported handling."""

    def __init__(self) -> None:
        self._parsers: dict[str, Callable[[str | Path], ParsedDocument]] = {}

    def register(self, parser: object) -> None:
        extensions = getattr(parser, "supported_extensions")
        parse = getattr(parser, "parse")
        for extension in extensions:
            self._parsers[str(extension).lower()] = parse

    def parse(self, path: str | Path) -> ParsedDocument:
        p = Path(path)
        parser = self._parsers.get(p.suffix.lower())
        if parser is None:
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream"),
                source_path=p,
                status=ParseStatus.UNSUPPORTED,
                metadata={"parser": "unsupported", "extension": p.suffix.lower()},
                errors=["unsupported_file_type"],
            )
        try:
            return parser(p)
        except Exception as exc:  # noqa: BLE001 - parser failures must not crash orchestration
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream"),
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "registry"},
                errors=[str(exc)],
            )


def default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PlainTextParser())
    registry.register(PdfTextParser())
    return registry
