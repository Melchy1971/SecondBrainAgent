"""Document Center core: preview building, import queue, tags, history, monitor.

Builds on ``secondbrain.document_understanding.parsers`` which already returns a
controlled ``ParsedDocument`` (status FAILED/UNSUPPORTED/OCR_REQUIRED) instead of
raising, so faulty files surface as an error state rather than crashing the GUI.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from secondbrain.document_understanding.parser_contract import ParsedDocument, ParseStatus
from secondbrain.document_understanding.parsers import MIME_BY_EXTENSION, default_parser_registry

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
_MARKDOWN_SUFFIXES = {".md", ".markdown"}
_TEXT_SUFFIXES = {".txt", ".log", ".csv", ".json"}
_OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx"}
_PDF_SUFFIXES = {".pdf"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PreviewKind(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF = "pdf"
    IMAGE = "image"
    OFFICE = "office"
    ERROR = "error"


class OcrStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    PENDING = "pending"
    DONE = "done"
    UNAVAILABLE = "unavailable"


class ItemState(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    READY = "ready"
    ERROR = "error"


@dataclass
class PreviewResult:
    doc_id: str
    path: str
    kind: PreviewKind
    title: str
    preview_text: str
    metadata: dict[str, Any]
    parse_status: str
    ocr_status: OcrStatus
    page_count: int = 0
    parser_errors: list[str] = field(default_factory=list)

    @property
    def is_error(self) -> bool:
        return self.kind == PreviewKind.ERROR

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "path": self.path,
            "kind": self.kind.value,
            "title": self.title,
            "preview_text": self.preview_text,
            "metadata": self.metadata,
            "parse_status": self.parse_status,
            "ocr_status": self.ocr_status.value,
            "page_count": self.page_count,
            "parser_errors": self.parser_errors,
            "is_error": self.is_error,
        }


def _kind_for(path: Path, parsed: ParsedDocument) -> PreviewKind:
    if parsed.status in (ParseStatus.FAILED, ParseStatus.UNSUPPORTED):
        return PreviewKind.ERROR
    suffix = path.suffix.lower()
    if suffix in _PDF_SUFFIXES:
        return PreviewKind.PDF
    if suffix in _IMAGE_SUFFIXES:
        return PreviewKind.IMAGE
    if suffix in _MARKDOWN_SUFFIXES:
        return PreviewKind.MARKDOWN
    if suffix in _OFFICE_SUFFIXES:
        return PreviewKind.OFFICE
    return PreviewKind.TEXT


def _ocr_for(path: Path, parsed: ParsedDocument, kind: PreviewKind) -> OcrStatus:
    if parsed.status == ParseStatus.OCR_REQUIRED:
        return OcrStatus.REQUIRED
    if kind == PreviewKind.IMAGE:
        return OcrStatus.DONE if parsed.text.strip() else OcrStatus.PENDING
    if kind == PreviewKind.PDF and not parsed.text.strip():
        return OcrStatus.REQUIRED
    return OcrStatus.NOT_REQUIRED


class PreviewBuilder:
    """Turns a file into a renderable, non-blocking PreviewResult."""

    def __init__(self, registry=None, *, max_chars: int = 20000) -> None:
        self.registry = registry or default_parser_registry()
        self.max_chars = max_chars

    def build(self, path: str | Path, *, doc_id: str | None = None) -> PreviewResult:
        p = Path(path)
        doc_id = doc_id or f"doc:{p.name}"
        if not p.exists() or not p.is_file():
            return PreviewResult(doc_id, str(p), PreviewKind.ERROR, p.name, "",
                                 {"reason": "file_not_found"}, "failed", OcrStatus.UNAVAILABLE,
                                 parser_errors=["file_not_found"])
        parsed = self.registry.parse(p)
        kind = _kind_for(p, parsed)
        ocr = _ocr_for(p, parsed, kind)
        metadata = {
            "mime_type": parsed.mime_type or MIME_BY_EXTENSION.get(p.suffix.lower(), "application/octet-stream"),
            "bytes": p.stat().st_size,
            "chars": parsed.char_count,
            **dict(parsed.metadata),
        }
        preview_text = "" if kind in (PreviewKind.IMAGE, PreviewKind.ERROR) else parsed.text[: self.max_chars]
        return PreviewResult(
            doc_id=doc_id,
            path=str(p),
            kind=kind,
            title=parsed.title or p.name,
            preview_text=preview_text,
            metadata=metadata,
            parse_status=parsed.status.value,
            ocr_status=ocr,
            page_count=parsed.page_count,
            parser_errors=list(parsed.errors),
        )


@dataclass
class ImportItem:
    id: str
    path: str
    state: ItemState = ItemState.QUEUED
    doc_id: str | None = None
    error: str | None = None
    preview: PreviewResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "path": self.path, "state": self.state.value,
                "doc_id": self.doc_id, "error": self.error}


class JobMonitor:
    """Import status feed. The GUI Job Monitor reads these entries."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._entries: list[dict[str, Any]] = []

    def record(self, item: ImportItem) -> None:
        entry = {"ts": _now(), "id": item.id, "path": item.path, "state": item.state.value, "error": item.error}
        self._entries.append(entry)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)


class TagStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, list[str]] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, doc_id: str) -> list[str]:
        return list(self._data.get(doc_id, []))

    def set(self, doc_id: str, tags: list[str]) -> list[str]:
        self._data[doc_id] = sorted({t.strip() for t in tags if t.strip()})
        self._save()
        return self._data[doc_id]

    def add(self, doc_id: str, tag: str) -> list[str]:
        return self.set(doc_id, self.get(doc_id) + [tag])

    def remove(self, doc_id: str, tag: str) -> list[str]:
        return self.set(doc_id, [t for t in self.get(doc_id) if t != tag])


class DocumentHistory:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record(self, doc_id: str, event: str, **detail: Any) -> None:
        entry = {"ts": _now(), "doc_id": doc_id, "event": event, "detail": detail}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    def for_document(self, doc_id: str) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                if entry.get("doc_id") == doc_id:
                    out.append(entry)
        return out


class ImportQueue:
    """Multi-file import queue with a non-blocking worker thread.

    ``enqueue`` accepts one or many paths (drag & drop drops a list). ``process_all``
    runs synchronously (used by tests); ``start_async`` runs on a worker thread and
    posts each finished item back through a scheduler so the GUI never blocks.
    """

    def __init__(self, preview_builder: PreviewBuilder | None = None, *,
                 monitor: JobMonitor | None = None, history: DocumentHistory | None = None,
                 on_indexed: Callable[[PreviewResult], None] | None = None) -> None:
        self.preview = preview_builder or PreviewBuilder()
        self.monitor = monitor or JobMonitor()
        self.history = history
        self.on_indexed = on_indexed
        self._items: list[ImportItem] = []

    def enqueue(self, paths: str | Path | list) -> list[ImportItem]:
        if isinstance(paths, (str, Path)):
            paths = [paths]
        added = []
        for path in paths:
            item = ImportItem(id=uuid.uuid4().hex[:10], path=str(path))
            self._items.append(item)
            self.monitor.record(item)
            added.append(item)
        return added

    def pending(self) -> list[ImportItem]:
        return [i for i in self._items if i.state == ItemState.QUEUED]

    def items(self) -> list[ImportItem]:
        return list(self._items)

    def _process(self, item: ImportItem) -> ImportItem:
        item.state = ItemState.PARSING
        self.monitor.record(item)
        preview = self.preview.build(item.path)
        item.preview = preview
        item.doc_id = preview.doc_id
        if preview.is_error:
            item.state = ItemState.ERROR
            item.error = "; ".join(preview.parser_errors) or "parse_failed"
        else:
            item.state = ItemState.READY
            if self.on_indexed:
                self.on_indexed(preview)
        self.monitor.record(item)
        if self.history:
            self.history.record(item.doc_id, "imported", state=item.state.value,
                                kind=preview.kind.value, ocr=preview.ocr_status.value)
        return item

    def process_all(self) -> list[ImportItem]:
        return [self._process(item) for item in self.pending()]

    def start_async(self, on_item: Callable[[ImportItem], None] | None = None,
                    scheduler: Callable[[Callable[[], None]], None] | None = None) -> threading.Thread:
        def _schedule(fn: Callable[[], None]) -> None:
            (scheduler or (lambda f: f()))(fn)

        def _run() -> None:
            for item in self.pending():
                processed = self._process(item)
                if on_item:
                    _schedule(lambda it=processed: on_item(it))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
