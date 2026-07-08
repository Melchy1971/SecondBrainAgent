from pathlib import Path

from secondbrain.document_understanding import (
    ParsedDocumentIngestionService,
    ParseStatus,
    build_parsed_document,
    default_parser_registry,
    normalize_text,
)


class FakeRuntime:
    def __init__(self):
        self.calls = []

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain"):
        self.calls.append((title, text, source_path, mime_type))
        return {"ok": True, "document_id": "doc-1", "chunks": 1}


def test_normalize_text_preserves_paragraphs_and_collapses_noise():
    raw = "  Alpha\t Beta  \r\n\r\n\r\n Gamma   Delta  "
    assert normalize_text(raw) == "Alpha Beta\n\nGamma Delta"


def test_build_parsed_document_sets_empty_status_for_blank_text():
    parsed = build_parsed_document(title="x", text="   ", mime_type="text/plain")
    assert parsed.status == ParseStatus.EMPTY
    assert parsed.ok is False
    assert parsed.to_ingestion_payload()["metadata"]["parse_status"] == "empty"


def test_default_registry_parses_text_file(tmp_path: Path):
    file_path = tmp_path / "note.md"
    file_path.write_text("# Title\n\nBody", encoding="utf-8")
    parsed = default_parser_registry().parse(file_path)
    assert parsed.status == ParseStatus.PARSED
    assert parsed.mime_type == "text/markdown"
    assert "Body" in parsed.text
    assert parsed.metadata["parser"] == "plain_text"


def test_default_registry_returns_unsupported_without_throwing(tmp_path: Path):
    file_path = tmp_path / "archive.exe"
    file_path.write_bytes(b"binary")
    parsed = default_parser_registry().parse(file_path)
    assert parsed.status == ParseStatus.UNSUPPORTED
    assert parsed.errors == ("unsupported_file_type",)


def test_parsed_document_ingestion_service_skips_invalid_parse(tmp_path: Path):
    runtime = FakeRuntime()
    service = ParsedDocumentIngestionService(runtime)
    file_path = tmp_path / "archive.exe"
    file_path.write_bytes(b"binary")
    result = service.ingest_file(file_path)
    assert result.ingested is False
    assert result.ok is False
    assert result.to_dict()["parse_status"] == "unsupported"
    assert runtime.calls == []


def test_parsed_document_ingestion_service_submits_valid_text(tmp_path: Path):
    runtime = FakeRuntime()
    service = ParsedDocumentIngestionService(runtime)
    file_path = tmp_path / "note.txt"
    file_path.write_text("Hello SecondBrain", encoding="utf-8")
    result = service.ingest_file(file_path)
    assert result.ok is True
    assert result.ingested is True
    assert runtime.calls[0][0] == "note.txt"
    assert runtime.calls[0][1] == "Hello SecondBrain"
