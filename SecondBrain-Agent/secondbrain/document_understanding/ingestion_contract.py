"""P1.3.1 - Contract adapter between parsers and ingestion runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .parser_contract import ParsedDocument, ParseStatus
from .parsers import ParserRegistry, default_parser_registry


@runtime_checkable
class TextIngestionRuntime(Protocol):
    def ingest_text(self, title: str, text: str, source_path: str = "manual", mime_type: str = "text/plain") -> dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class ParsedIngestionResult:
    parsed: ParsedDocument
    ingested: bool
    result: dict[str, Any]

    @property
    def ok(self) -> bool:
        return self.parsed.ok and self.ingested and bool(self.result.get("ok", False))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "ingested": self.ingested,
            "parse_status": self.parsed.status.value,
            "title": self.parsed.title,
            "chars": self.parsed.char_count,
            "pages": self.parsed.page_count,
            "result": dict(self.result),
            "errors": list(self.parsed.errors),
        }


class ParsedDocumentIngestionService:
    """Parse files first, then call the existing text ingestion boundary."""

    def __init__(self, runtime: TextIngestionRuntime, registry: ParserRegistry | None = None) -> None:
        self.runtime = runtime
        self.registry = registry or default_parser_registry()

    def ingest_file(self, path: str | Path) -> ParsedIngestionResult:
        parsed = self.registry.parse(path)
        if parsed.status in {ParseStatus.UNSUPPORTED, ParseStatus.FAILED, ParseStatus.EMPTY, ParseStatus.OCR_REQUIRED}:
            return ParsedIngestionResult(parsed=parsed, ingested=False, result={"ok": False, "reason": parsed.status.value})
        payload = parsed.to_ingestion_payload()
        result = self.runtime.ingest_text(
            payload["title"],
            payload["text"],
            payload["source_path"],
            payload["mime_type"],
        )
        return ParsedIngestionResult(parsed=parsed, ingested=True, result=result)
