"""P1.3.4 - Multi-format parser orchestration.

This module provides a stable orchestration boundary above individual parsers.
It resolves parser selection by MIME type and extension, executes parsing without
leaking parser exceptions, and returns an audit-friendly result object for import,
UI, and release gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from .parser_contract import ParsedDocument, ParseStatus, build_parsed_document
from .parsers import (
    MIME_BY_EXTENSION,
    CsvParser,
    EmailParser,
    JsonParser,
    MarkdownParser,
    ParserValidationError,
    PdfTextParser,
    PlainTextParser,
)
from .pdf_facade import PdfOcrParserFacade


ParserCallable = Callable[[str | Path], ParsedDocument]


@dataclass(frozen=True, slots=True)
class ParserSelection:
    """Resolved parser decision for one file."""

    parser_name: str
    extension: str
    mime_type: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "parser_name": self.parser_name,
            "extension": self.extension,
            "mime_type": self.mime_type,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ParseOrchestrationResult:
    """Envelope returned by the parser orchestrator."""

    parsed: ParsedDocument
    selection: ParserSelection
    warnings: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.parsed.status == ParseStatus.PARSED and self.parsed.char_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.parsed.status.value,
            "title": self.parsed.title,
            "chars": self.parsed.char_count,
            "pages": self.parsed.page_count,
            "selection": self.selection.to_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.parsed.errors),
            "diagnostics": dict(self.diagnostics),
        }


class MultiFormatParserOrchestrator:
    """Select and execute document parsers by MIME type or extension.

    Selection order:
    1. explicit MIME type registration
    2. file extension registration
    3. deterministic unsupported result

    The orchestrator intentionally returns ``ParsedDocument`` failure states
    instead of raising parser exceptions. That keeps connector imports, batch jobs,
    and UI previews stable when one file is malformed.
    """

    def __init__(self) -> None:
        self._by_extension: dict[str, tuple[str, ParserCallable]] = {}
        self._by_mime: dict[str, tuple[str, ParserCallable]] = {}

    def register(
        self,
        parser: object,
        *,
        name: str | None = None,
        mime_types: Iterable[str] = (),
    ) -> None:
        parser_name = name or parser.__class__.__name__
        extensions: Iterable[str] = getattr(parser, "supported_extensions")
        parse: ParserCallable = getattr(parser, "parse")
        for extension in extensions:
            normalized = _normalize_extension(extension)
            self._by_extension[normalized] = (parser_name, parse)
        for mime_type in mime_types:
            if mime_type:
                self._by_mime[mime_type.lower()] = (parser_name, parse)

    def select(self, path: str | Path, mime_type: str | None = None) -> ParserSelection:
        p = Path(path)
        extension = _normalize_extension(p.suffix)
        resolved_mime = (mime_type or MIME_BY_EXTENSION.get(extension) or "application/octet-stream").lower()
        if mime_type and resolved_mime in self._by_mime:
            parser_name, _ = self._by_mime[resolved_mime]
            return ParserSelection(parser_name, extension, resolved_mime, "mime_type")
        if extension in self._by_extension:
            parser_name, _ = self._by_extension[extension]
            return ParserSelection(parser_name, extension, resolved_mime, "extension")
        return ParserSelection("unsupported", extension, resolved_mime, "unsupported")

    def parse(self, path: str | Path, mime_type: str | None = None) -> ParseOrchestrationResult:
        selection = self.select(path, mime_type)
        p = Path(path)
        parser_entry = None
        if selection.reason == "mime_type":
            parser_entry = self._by_mime.get(selection.mime_type)
        elif selection.reason == "extension":
            parser_entry = self._by_extension.get(selection.extension)

        if parser_entry is None:
            parsed = build_parsed_document(
                title=p.name,
                text="",
                mime_type=selection.mime_type,
                source_path=p,
                status=ParseStatus.UNSUPPORTED,
                metadata={"parser": "unsupported", "extension": selection.extension},
                errors=["unsupported_file_type"],
            )
            return ParseOrchestrationResult(parsed=parsed, selection=selection)

        parser_name, parser = parser_entry
        try:
            parsed = parser(p)
        except ParserValidationError as exc:
            parsed = build_parsed_document(
                title=p.name,
                text="",
                mime_type=selection.mime_type,
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": parser_name, "extension": selection.extension},
                errors=[str(exc)],
            )
        except Exception as exc:  # noqa: BLE001 - orchestration boundary
            parsed = build_parsed_document(
                title=p.name,
                text="",
                mime_type=selection.mime_type,
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": parser_name, "extension": selection.extension},
                errors=[f"parser_exception:{exc}"],
            )

        warnings = _derive_warnings(parsed)
        diagnostics = {
            "selected_by": selection.reason,
            "parser_name": parser_name,
            "source_exists": p.exists(),
        }
        return ParseOrchestrationResult(parsed=parsed, selection=selection, warnings=warnings, diagnostics=diagnostics)


def default_multi_format_orchestrator(*, enable_pdf_ocr_facade: bool = True) -> MultiFormatParserOrchestrator:
    orchestrator = MultiFormatParserOrchestrator()
    orchestrator.register(PlainTextParser(), mime_types=("text/plain",))
    orchestrator.register(MarkdownParser(), mime_types=("text/markdown", "text/x-markdown"))
    orchestrator.register(JsonParser(), mime_types=("application/json", "application/x-ndjson"))
    orchestrator.register(CsvParser(), mime_types=("text/csv",))
    orchestrator.register(EmailParser(), mime_types=("message/rfc822",))
    pdf_parser = PdfOcrParserFacade() if enable_pdf_ocr_facade else PdfTextParser()
    orchestrator.register(pdf_parser, name="PdfOcrParserFacade" if enable_pdf_ocr_facade else "PdfTextParser", mime_types=("application/pdf",))
    return orchestrator


def _normalize_extension(extension: str | None) -> str:
    value = (extension or "").lower().strip()
    if value and not value.startswith("."):
        value = f".{value}"
    return value


def _derive_warnings(parsed: ParsedDocument) -> tuple[str, ...]:
    warnings: list[str] = []
    if parsed.status == ParseStatus.OCR_REQUIRED:
        warnings.append("ocr_required")
    if parsed.status == ParseStatus.EMPTY:
        warnings.append("empty_document")
    if parsed.status == ParseStatus.PARSED and parsed.char_count < 20:
        warnings.append("very_short_text")
    return tuple(warnings)
