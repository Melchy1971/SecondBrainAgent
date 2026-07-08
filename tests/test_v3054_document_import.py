from __future__ import annotations

import json
import sqlite3
import zipfile
from pathlib import Path

import pytest

from secondbrain.document_understanding.orchestrator import ParseOrchestrationResult, default_multi_format_orchestrator
from secondbrain.document_understanding.parser_contract import ParseStatus, build_parsed_document
from secondbrain.importing import ImportService, StreamingImportService


@pytest.mark.parametrize("name,parser", [
    ("mail.pst", "PstParser"), ("mail.eml", "EmailParser"), ("file.pdf", "PdfOcrParserFacade"),
    ("file.docx", "DocxParser"), ("file.xlsx", "XlsxParser"), ("file.csv", "CsvParser"),
    ("file.txt", "PlainTextParser"), ("file.md", "MarkdownParser"),
])
def test_existing_parser_orchestrator_selects_document_formats(name, parser):
    selection = default_multi_format_orchestrator().select(name)
    assert selection.parser_name == parser


def test_eml_import_preserves_metadata_attachments_version_and_workspace(tmp_path):
    source = tmp_path / "message.eml"
    source.write_bytes(
        b"Subject: Test\r\nFrom: a@example.test\r\nTo: b@example.test\r\nMIME-Version: 1.0\r\n"
        b"Content-Type: multipart/mixed; boundary=x\r\n\r\n--x\r\nContent-Type: text/plain\r\n\r\nBody\r\n"
        b"--x\r\nContent-Type: text/plain\r\nContent-Disposition: attachment; filename=note.txt\r\n\r\nAttachment\r\n--x--\r\n"
    )
    service = ImportService(tmp_path)
    session = service.import_document(source, source="eml", workspace_id="mail", version="7")
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert session.imported_chats == 1
    assert metadata["schema"] == "secondbrain.document.v1"
    assert metadata["workspace"] == "mail" and metadata["version"] == "7"
    assert metadata["attachments"][0]["name"] == "note.txt"
    assert metadata["ocr_status"] == "not_required"


def test_ocr_required_document_is_imported_with_explicit_status(tmp_path):
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-1.4\n")
    service = StreamingImportService(tmp_path)
    parsed = build_parsed_document(title="scan.pdf", text="", mime_type="application/pdf", source_path=source,
                                   status=ParseStatus.OCR_REQUIRED, metadata={"parser": "pdf", "ocr_required": True})
    selected = service.document_parser.select(source)
    service.document_parser.parse = lambda _path: ParseOrchestrationResult(parsed, selected)  # type: ignore[method-assign]
    service.import_document(source, workspace_id="archive")
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert metadata["ocr_status"] == "required"
    assert metadata["document"]["parse_status"] == "ocr_required"


def test_versions_are_preserved_as_separate_documents(tmp_path):
    source = tmp_path / "versioned.txt"
    source.write_text("first", encoding="utf-8")
    service = StreamingImportService(tmp_path)
    service.import_document(source, workspace_id="docs", version="1")
    source.write_text("second", encoding="utf-8")
    service.import_document(source, workspace_id="docs", version="2")
    with sqlite3.connect(service.db_path) as connection:
        rows = [json.loads(row[0]) for row in connection.execute("SELECT metadata_json FROM documents ORDER BY id")]
        versions = connection.execute("SELECT version_number,content FROM document_versions ORDER BY version_number").fetchall()
    assert len(rows) == 1
    assert versions == [(1, "first"), (2, "second")]
    assert rows[0]["version"] == "2"


@pytest.mark.parametrize("provider,filename,content", [
    ("obsidian", "note.md", "---\ntags: [x]\n---\n# Note"),
    ("paperless", "metadata.json", '{"title":"Paperless","archive_serial_number":7}'),
])
def test_workspace_directory_sources_use_same_import_service(tmp_path, provider, filename, content):
    root = tmp_path / provider
    root.mkdir()
    (root / filename).write_text(content, encoding="utf-8")
    service = StreamingImportService(tmp_path)
    sessions = service.import_workspace(root, source=provider, workspace_id="knowledge")
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert len(sessions) == 1
    assert metadata["source"]["provider"] == provider
    assert metadata["workspace"] == "knowledge"


@pytest.mark.parametrize("provider", ["notion", "onenote"])
def test_workspace_zip_exports_use_existing_parsers(provider, tmp_path):
    archive = tmp_path / f"{provider}.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("Export/page.md", f"# {provider.title()}\n\nContent")
    service = StreamingImportService(tmp_path)
    sessions = service.import_workspace(archive, source=provider, workspace_id="imports")
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert sessions[0].imported_chats == 1
    assert metadata["metadata"]["archive_member"] == "Export/page.md"
    assert metadata["workspace"] == "imports"


def test_import_service_is_the_single_existing_service():
    assert ImportService is StreamingImportService
