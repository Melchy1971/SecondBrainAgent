"""P1.3.2 - Concrete document parsers with robust validation.

The parser layer stays dependency-light and deterministic. Optional heavyweight
readers such as PyMuPDF/pypdf remain behind explicit failure states instead of
leaking exceptions into connector/import/RAG orchestration.
"""

from __future__ import annotations

import csv
import json
import stat
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

from .parser_contract import ParsedDocument, ParsedPage, ParseStatus, build_parsed_document, normalize_text


MIME_BY_EXTENSION = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".jsonl": "application/x-ndjson",
    ".eml": "message/rfc822",
    ".pst": "application/vnd.ms-outlook",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


MAX_TEXT_BYTES = 25 * 1024 * 1024
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_JSON_BYTES = 10 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 500_000
MAX_JSONL_RECORDS = 100_000
MAX_ARCHIVE_MEMBERS = 10_000
MAX_ARCHIVE_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 100
MAX_ARCHIVE_PATH_DEPTH = 16
MAX_PDF_PAGES = 2_000
MAX_PARSED_CHARS = 10_000_000
MAX_PST_FOLDERS = 10_000
MAX_PST_MESSAGES = 100_000


class ParserValidationError(ValueError):
    """Raised for controlled parser precondition failures."""


def _ensure_existing_file(path: str | Path) -> Path:
    p = Path(path)
    if ".." in p.parts:
        raise ParserValidationError("path_traversal_not_allowed")
    if p.is_symlink():
        raise ParserValidationError("symlink_not_allowed")
    if not p.exists():
        raise ParserValidationError("file_not_found")
    if not p.is_file():
        raise ParserValidationError("not_a_file")
    if p.stat().st_size > MAX_FILE_BYTES:
        raise ParserValidationError("file_size_limit_exceeded")
    return p


def _read_text(path: Path) -> str:
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ParserValidationError("file_too_large_for_text_parser")
    return path.read_text(encoding="utf-8", errors="replace")


def _validate_json_structure(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    nodes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise ParserValidationError("json_node_limit_exceeded")
        if depth > MAX_JSON_DEPTH:
            raise ParserValidationError("json_depth_limit_exceeded")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def _validate_zip_container(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise ParserValidationError("invalid_archive") from exc
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ParserValidationError("archive_member_limit_exceeded")

    total_uncompressed = 0
    for member in members:
        member_path = PurePosixPath(member.filename.replace("\\", "/"))
        if member_path.is_absolute() or ".." in member_path.parts:
            raise ParserValidationError("archive_path_traversal")
        if len(member_path.parts) > MAX_ARCHIVE_PATH_DEPTH:
            raise ParserValidationError("archive_depth_limit_exceeded")
        member_mode = member.external_attr >> 16
        if stat.S_ISLNK(member_mode):
            raise ParserValidationError("archive_symlink_not_allowed")
        if member.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise ParserValidationError("archive_member_size_limit_exceeded")
        total_uncompressed += member.file_size
        if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ParserValidationError("archive_size_limit_exceeded")
        if member.file_size >= 1024 * 1024:
            ratio = member.file_size / max(1, member.compress_size)
            if ratio > MAX_ARCHIVE_COMPRESSION_RATIO:
                raise ParserValidationError("archive_compression_ratio_exceeded")


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
        if p.stat().st_size > MAX_JSON_BYTES:
            raise ParserValidationError("json_size_limit_exceeded")
        raw = _read_text(p)
        try:
            if p.suffix.lower() == ".jsonl":
                records = []
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    if len(records) >= MAX_JSONL_RECORDS:
                        raise ParserValidationError("jsonl_record_limit_exceeded")
                    record = json.loads(line)
                    _validate_json_structure(record)
                    records.append(record)
                text = "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records)
                metadata = {"parser": "jsonl", "records": len(records), "bytes": p.stat().st_size}
                mime_type = "application/x-ndjson"
            else:
                data = json.loads(raw) if raw.strip() else None
                _validate_json_structure(data)
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
        attachments = []
        for part in message.iter_attachments():
            payload = part.get_payload(decode=True) or b""
            attachments.append({"name": part.get_filename() or "attachment", "mime_type": part.get_content_type(), "bytes": len(payload)})
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
            metadata={"parser": "email", "bytes": p.stat().st_size, "attachments": attachments,
                      "message_id": str(message.get("message-id") or ""), "date": str(message.get("date") or "")},
        )


class PstParser:
    """PST parser using the established parser contract and optional pypff reader."""

    supported_extensions = {".pst"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        try:
            import pypff  # type: ignore[import-not-found]
        except Exception as exc:
            return build_parsed_document(title=p.name, text="", mime_type=MIME_BY_EXTENSION[".pst"], source_path=p,
                status=ParseStatus.FAILED, metadata={"parser": "pypff", "bytes": p.stat().st_size},
                errors=[f"pst_reader_missing:{type(exc).__name__}"])
        store = pypff.file()
        lines: list[str] = []
        attachments: list[dict[str, Any]] = []
        counters = {"folders": 0, "messages": 0, "chars": 0}
        try:
            store.open(str(p))
            def visit(folder, depth: int = 0) -> None:
                if depth > MAX_ARCHIVE_PATH_DEPTH:
                    raise ParserValidationError("pst_depth_limit_exceeded")
                counters["folders"] += 1
                if counters["folders"] > MAX_PST_FOLDERS:
                    raise ParserValidationError("pst_folder_limit_exceeded")
                for index in range(folder.number_of_sub_messages):
                    counters["messages"] += 1
                    if counters["messages"] > MAX_PST_MESSAGES:
                        raise ParserValidationError("pst_message_limit_exceeded")
                    message = folder.get_sub_message(index)
                    body = str(message.plain_text_body or "")
                    counters["chars"] += len(body)
                    if counters["chars"] > MAX_PARSED_CHARS:
                        raise ParserValidationError("parsed_text_limit_exceeded")
                    lines.extend((f"## {message.subject or 'Message'}", f"From: {message.sender_name or ''}", body, ""))
                    for attachment_index in range(message.number_of_attachments):
                        attachment = message.get_attachment(attachment_index)
                        attachments.append({"name": attachment.name or f"attachment-{attachment_index + 1}", "bytes": attachment.size})
                for index in range(folder.number_of_sub_folders):
                    visit(folder.get_sub_folder(index), depth + 1)
            visit(store.get_root_folder())
        except ParserValidationError:
            raise
        except Exception as exc:
            return build_parsed_document(title=p.name, text="", mime_type=MIME_BY_EXTENSION[".pst"], source_path=p,
                status=ParseStatus.FAILED, metadata={"parser": "pypff", "bytes": p.stat().st_size}, errors=[f"pst_parse_failed:{exc}"])
        finally:
            store.close()
        return build_parsed_document(title=p.name, text="\n".join(lines), mime_type=MIME_BY_EXTENSION[".pst"], source_path=p,
            metadata={"parser": "pypff", "bytes": p.stat().st_size, "attachments": attachments})


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
                if doc.page_count > MAX_PDF_PAGES:
                    raise ParserValidationError("pdf_page_limit_exceeded")
                parsed_chars = 0
                for index, page in enumerate(doc, start=1):
                    page_text = page.get_text("text") or ""
                    parsed_chars += len(page_text)
                    if parsed_chars > MAX_PARSED_CHARS:
                        raise ParserValidationError("pdf_text_limit_exceeded")
                    pages.append(ParsedPage(number=index, text=page_text))
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
        except ParserValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 - parser fallback boundary
            errors.append(f"pymupdf:{exc}")

        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]

            reader = PdfReader(str(p))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ParserValidationError("pdf_page_limit_exceeded")
            parsed_chars = 0
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                parsed_chars += len(page_text)
                if parsed_chars > MAX_PARSED_CHARS:
                    raise ParserValidationError("pdf_text_limit_exceeded")
                pages.append(ParsedPage(number=index, text=page_text))
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
        except ParserValidationError:
            raise
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


class DocxParser:
    """DOCX parser delegating extraction to the existing office import layer."""

    supported_extensions = {".docx"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        mime_type = MIME_BY_EXTENSION[".docx"]
        try:
            import docx  # type: ignore[import-not-found]  # noqa: F401
        except Exception as exc:  # noqa: BLE001 - optional dependency boundary
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=mime_type,
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "docx", "dependency": "python-docx", "bytes": p.stat().st_size},
                errors=[f"docx_reader_missing:{type(exc).__name__}"],
            )
        _validate_zip_container(p)
        from secondbrain.office_import import extract_docx

        text = extract_docx(p)
        return build_parsed_document(
            title=p.name,
            text=text,
            mime_type=mime_type,
            source_path=p,
            metadata={"parser": "docx", "bytes": p.stat().st_size},
        )


class XlsxParser:
    """XLSX parser delegating extraction to the existing office import layer."""

    supported_extensions = {".xlsx"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        mime_type = MIME_BY_EXTENSION[".xlsx"]
        try:
            import openpyxl  # type: ignore[import-not-found]  # noqa: F401
        except Exception as exc:  # noqa: BLE001 - optional dependency boundary
            return build_parsed_document(
                title=p.name,
                text="",
                mime_type=mime_type,
                source_path=p,
                status=ParseStatus.FAILED,
                metadata={"parser": "xlsx", "dependency": "openpyxl", "bytes": p.stat().st_size},
                errors=[f"xlsx_reader_missing:{type(exc).__name__}"],
            )
        _validate_zip_container(p)
        from secondbrain.office_import import extract_xlsx

        text = extract_xlsx(p)
        return build_parsed_document(
            title=p.name,
            text=text,
            mime_type=mime_type,
            source_path=p,
            metadata={"parser": "xlsx", "bytes": p.stat().st_size},
        )


class ImageParser:
    """PNG/JPG parser: dimensions via Pillow, text only via optional OCR engine."""

    supported_extensions = {".png", ".jpg", ".jpeg"}

    def parse(self, path: str | Path) -> ParsedDocument:
        p = _ensure_existing_file(path)
        mime_type = MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream")
        metadata: dict[str, object] = {"parser": "image", "bytes": p.stat().st_size}
        image = None
        try:
            from PIL import Image  # type: ignore[import-not-found]

            image = Image.open(p)
            metadata.update({"width": image.width, "height": image.height, "format": image.format})
        except Exception as exc:  # noqa: BLE001 - optional dependency boundary
            metadata["pillow"] = f"unavailable:{type(exc).__name__}"

        try:
            if image is not None:
                import pytesseract  # type: ignore[import-not-found]

                text = pytesseract.image_to_string(image)
                if text.strip():
                    metadata["ocr_engine"] = "pytesseract"
                    return build_parsed_document(
                        title=p.name,
                        text=text,
                        mime_type=mime_type,
                        source_path=p,
                        metadata=metadata,
                    )
        except Exception as exc:  # noqa: BLE001 - OCR stays optional
            metadata["ocr_engine"] = f"unavailable:{type(exc).__name__}"
        finally:
            if image is not None:
                image.close()

        return build_parsed_document(
            title=p.name,
            text="",
            mime_type=mime_type,
            source_path=p,
            status=ParseStatus.OCR_REQUIRED,
            metadata=metadata,
            errors=["image_text_requires_ocr"],
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
    registry.register(PstParser())
    registry.register(PdfTextParser())
    registry.register(DocxParser())
    registry.register(XlsxParser())
    registry.register(ImageParser())
    return registry
