"""P1.3.2 - Concrete document parsers with robust validation.

The parser layer stays dependency-light and deterministic. Optional heavyweight
readers such as PyMuPDF/pypdf remain behind explicit failure states instead of
leaking exceptions into connector/import/RAG orchestration.
"""

from __future__ import annotations

import csv
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Callable, Iterable

from .parser_contract import ParsedDocument, ParsedPage, ParseStatus, build_parsed_document, normalize_text


MIME_BY_EXTENSION = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".eml": "message/rfc822",
    ".pdf": "application/pdf",
}


MAX_TEXT_BYTES = 25 * 1024 * 1024


class ParserValidationError(ValueError):
    """Raised for controlled parser precondition failures."""


def _ensure_existing_file(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise ParserValidationError("file_not_found")
    if not p.is_file():
        raise ParserValidationError("not_a_file")
    return p


def _read_text(path: Path) -> str:
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ParserValidationError("file_too_large_for_text_parser")
    return path.read_text(encoding="utf-8", errors="replace")


class PlainTextParser:
    """Parser for plain UTF-8 compatible text documents."""

    supported_extensions = {".txt"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        text = _read_text(p)
        return build_parsed_document(
            title=p.name,
            text=text,
            mime_type="text/plain",
            source_path=p,
            metadata={"parser": "plain_text", "bytes": p.stat().st_size},
        )


class MarkdownParser:
    """Markdown parser that preserves readable text and strips common metadata fences."""

    supported_extensions = {".md", ".markdown"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        text = _read_text(p)
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) == 3:
                text = parts[2]
        return build_parsed_document(
            title=p.name,
            text=text,
            mime_type="text/markdown",
            source_path=p,
            metadata={"parser": "plain_text", "parser_detail": "markdown", "bytes": p.stat().st_size},
        )


class JsonParser:
    """JSON/JSONL parser returning deterministic, searchable plain text."""

    supported_extensions = {".json", ".jsonl"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        raw = _read_text(p)
        try:
            if p.suffix.lower() == ".jsonl":
                records = [json.loads(line) for line in raw.splitlines() if line.strip()]
                text = "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records)
                metadata = {"parser": "jsonl", "records": len(records), "bytes": p.stat().st_size}
                mime_type = "application/x-ndjson"
            else:
                data = json.loads(raw) if raw.strip() else None
                text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) if data is not None else ""
                metadata = {"parser": "json", "bytes": p.stat().st_size}
                mime_type = "application/json"
        except json.JSONDecodeError as exc:
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "application/json"),
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "json"},
                errors=[f"invalid_json:{exc.msg}"],
            )
        return build_parsed_document(title=p.name, text=text, mime_type=mime_type, source_path=p, metadata=metadata)


class CsvParser:
    """CSV parser that converts rows into stable tab-separated text."""

    supported_extensions = {".csv"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        raw = _read_text(p)
        try:
            sample = raw[:4096]
            dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        except csv.Error:
            dialect = csv.excel
        rows: list[str] = []
        try:
            for row in csv.reader(raw.splitlines(), dialect):
                rows.append("\t".join(normalize_text(cell) for cell in row))
        except csv.Error as exc:
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type="text/csv",
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "csv"},
                errors=[f"invalid_csv:{exc}"],
            )
        return build_parsed_document(
            title=p.name,
            text="\n".join(rows),
            mime_type="text/csv",
            source_path=p,
            metadata={"parser": "csv", "rows": len(rows), "bytes": p.stat().st_size},
        )


class EmailParser:
    """RFC822 .eml parser extracting headers and text body."""

    supported_extensions = {".eml"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        message = BytesParser(policy=policy.default).parsebytes(p.read_bytes())
        subject = str(message.get("subject") or p.name)
        parts: list[str] = []
        for header in ("from", "to", "cc", "date", "subject"):
            value = message.get(header)
            if value:
                parts.append(f"{header.title()}: {value}")
        body = message.get_body(preferencelist=("plain",))
        if body is not None:
            parts.append(body.get_content())
        elif not message.is_multipart():
            payload = message.get_payload(decode=True)
            if isinstance(payload, bytes):
                parts.append(payload.decode(message.get_content_charset() or "utf-8", errors="replace"))
            elif isinstance(payload, str):
                parts.append(payload)
        return build_parsed_document(
            title=subject,
            text="\n\n".join(parts),
            mime_type="message/rfc822",
            source_path=p,
            metadata={"parser": "email", "bytes": p.stat().st_size},
        )


class PdfTextParser:
    """PDF parser with optional PyMuPDF/pypdf support and explicit failure state."""

    supported_extensions = {".pdf"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        errors: list[str] = []
        pages: list[ParsedPage] = []

        try:
            import fitz  # type: ignore[import-not-found]

            with fitz.open(p) as doc:
                for index, page in enumerate(doc, start=1):
                    pages.append(ParsedPage(number=index, text=page.get_text("text") or ""))
            parsed = build_parsed_document(
                title=p.name,
                text=None,
                mime_type="application/pdf",
                source_path=p,
                pages=pages,
                metadata={"parser": "pymupdf", "bytes": p.stat().st_size},
            )
            if parsed.char_count == 0:
                return build_parsed_document(
                    title=p.name,
                    text="",
                    mime_type="application/pdf",
                    source_path=p,
                    pages=pages,
                    metadata={"parser": "pymupdf", "bytes": p.stat().st_size, "ocr_required": True},
                    errors=["pdf_text_empty_ocr_required"],
                    status=ParseStatus.OCR_REQUIRED,
                )
            return parsed
        except Exception as exc:  # noqa: BLE001 - parser fallback boundary
            errors.append(f"pymupdf:{exc}")

        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]

            reader = PdfReader(str(p))
            for index, page in enumerate(reader.pages, start=1):
                pages.append(ParsedPage(number=index, text=page.extract_text() or ""))
            parsed = build_parsed_document(
                title=p.name,
                text=None,
                mime_type="application/pdf",
                source_path=p,
                pages=pages,
                metadata={"parser": "pypdf", "bytes": p.stat().st_size},
                errors=errors,
            )
            if parsed.char_count == 0:
                return build_parsed_document(
                    title=p.name,
                    text="",
                    mime_type="application/pdf",
                    source_path=p,
                    pages=pages,
                    metadata={"parser": "pypdf", "bytes": p.stat().st_size, "ocr_required": True},
                    errors=[*errors, "pdf_text_empty_ocr_required"],
                    status=ParseStatus.OCR_REQUIRED,
                )
            return parsed
        except Exception as exc:  # noqa: BLE001
            errors.append(f"pypdf:{exc}")

        return build_parsed_document(
            title=p.name,
            text="",
            mime_type="application/pdf",
            source_path=p,
            metadata={"parser": "pdf_text", "bytes": p.stat().st_size if p.exists() else 0},
            errors=errors,
            status=ParseStatus.FAILED,
        )


class ParserRegistry:
    """Extension based parser registry with deterministic unsupported handling."""

    def __init__(self) -> None:
        self._parsers: dict[str, Callable[[str | Path], ParsedDocument]] = {}

    def register(self, parser: object) -> None:
        extensions: Iterable[str] = getattr(parser, "supported_extensions")
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
        except ParserValidationError as exc:
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream"),
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "validation", "extension": p.suffix.lower()},
                errors=[str(exc)],
            )
        except Exception as exc:  # noqa: BLE001 - parser failures must not crash orchestration
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream"),
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "registry", "extension": p.suffix.lower()},
                errors=[str(exc)],
            )


def default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PlainTextParser())
    registry.register(MarkdownParser())
    registry.register(JsonParser())
    registry.register(CsvParser())
    registry.register(EmailParser())
    registry.register(PdfTextParser())
    return registry
