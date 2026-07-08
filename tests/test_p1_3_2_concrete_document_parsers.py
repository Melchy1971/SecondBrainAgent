from pathlib import Path

from secondbrain.document_understanding import (
    CsvParser,
    DocumentUnderstandingRuntime,
    JsonParser,
    MarkdownParser,
    ParseStatus,
    default_parser_registry,
)


class FakeRuntime:
    def __init__(self):
        self.calls = []

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain"):
        self.calls.append((title, text, source_path, mime_type))
        return {"ok": True, "document_id": "doc-1"}


def test_markdown_parser_strips_frontmatter(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("---\ntags: [x]\n---\n# Heading\n\nBody", encoding="utf-8")
    parsed = MarkdownParser().parse(path)
    assert parsed.status == ParseStatus.PARSED
    assert parsed.metadata["parser_detail"] == "markdown"
    assert "tags:" not in parsed.text
    assert "Body" in parsed.text


def test_json_parser_returns_sorted_searchable_text(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text('{"b": 2, "a": 1}', encoding="utf-8")
    parsed = JsonParser().parse(path)
    assert parsed.status == ParseStatus.PARSED
    assert parsed.mime_type == "application/json"
    assert parsed.text.index('"a"') < parsed.text.index('"b"')


def test_json_parser_reports_invalid_json_without_throwing(tmp_path: Path):
    path = tmp_path / "broken.json"
    path.write_text('{"a":', encoding="utf-8")
    parsed = default_parser_registry().parse(path)
    assert parsed.status == ParseStatus.FAILED
    assert parsed.errors[0].startswith("invalid_json:")


def test_jsonl_parser_counts_records(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"id": 2}\n{"id": 1}\n', encoding="utf-8")
    parsed = default_parser_registry().parse(path)
    assert parsed.status == ParseStatus.PARSED
    assert parsed.metadata["parser"] == "jsonl"
    assert parsed.metadata["records"] == 2


def test_csv_parser_converts_rows_to_tab_separated_text(tmp_path: Path):
    path = tmp_path / "table.csv"
    path.write_text("name,score\nalpha,10\n", encoding="utf-8")
    parsed = CsvParser().parse(path)
    assert parsed.status == ParseStatus.PARSED
    assert "name score" in parsed.text
    assert parsed.metadata["rows"] == 2


def test_email_parser_extracts_headers_and_plain_body(tmp_path: Path):
    path = tmp_path / "mail.eml"
    path.write_text(
        "From: a@example.test\nTo: b@example.test\nSubject: Hello\nDate: Tue, 23 Jun 2026 08:00:00 +0200\n\nBody text",
        encoding="utf-8",
    )
    parsed = default_parser_registry().parse(path)
    assert parsed.status == ParseStatus.PARSED
    assert parsed.title == "Hello"
    assert "From: a@example.test" in parsed.text
    assert "Body text" in parsed.text


def test_registry_reports_missing_file_as_failed(tmp_path: Path):
    parsed = default_parser_registry().parse(tmp_path / "missing.txt")
    assert parsed.status == ParseStatus.FAILED
    assert parsed.errors == ("file_not_found",)


def test_document_understanding_runtime_ingests_valid_file(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("Runtime body", encoding="utf-8")
    runtime = DocumentUnderstandingRuntime(FakeRuntime())
    result = runtime.ingest_file(path)
    assert result["ok"] is True
    assert result["parse_status"] == "parsed"
