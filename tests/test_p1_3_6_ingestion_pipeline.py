from __future__ import annotations

from pathlib import Path

from secondbrain.document_understanding.ingestion_pipeline import DocumentIngestionPipeline, IngestionPipelineStatus


class RecordingRuntime:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.calls = []

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain", metadata=None):
        self.calls.append(
            {
                "title": title,
                "text": text,
                "source_path": source_path,
                "mime_type": mime_type,
                "metadata": metadata or {},
            }
        )
        return {"ok": self.ok, "document_id": "doc-1"} if self.ok else {"ok": False, "reason": "store_failed"}


class LegacyRuntime:
    def __init__(self) -> None:
        self.calls = []

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain"):
        self.calls.append((title, text, source_path, mime_type))
        return {"ok": True, "legacy": True}


class FailingRuntime:
    def ingest_text(self, *args, **kwargs):
        raise RuntimeError("database_down")


def test_pipeline_ingests_accepted_text_file(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("This document contains enough searchable content for ingestion.", encoding="utf-8")
    runtime = RecordingRuntime()

    result = DocumentIngestionPipeline(runtime).ingest_file(path)

    assert result.ok is True
    assert result.status == IngestionPipelineStatus.INGESTED_WITH_REVIEW
    assert result.ingested is True
    assert len(runtime.calls) == 1
    assert runtime.calls[0]["metadata"]["quality_decision"] == "review"
    assert runtime.calls[0]["metadata"]["parser_selection"]["parser_name"] == "PlainTextParser"


def test_pipeline_rejects_unsupported_file_without_side_effect(tmp_path: Path):
    path = tmp_path / "archive.bin"
    path.write_bytes(b"unsupported")
    runtime = RecordingRuntime()

    result = DocumentIngestionPipeline(runtime).ingest_file(path)

    assert result.ok is False
    assert result.status == IngestionPipelineStatus.REJECTED
    assert result.ingested is False
    assert runtime.calls == []
    assert "unsupported_type" in result.to_dict()["quality"]["reject_reasons"]


def test_pipeline_marks_review_but_still_ingests_short_valid_content(tmp_path: Path):
    path = tmp_path / "short.txt"
    path.write_text("small but valid words", encoding="utf-8")
    runtime = RecordingRuntime()

    result = DocumentIngestionPipeline(runtime).ingest_file(path)

    assert result.ok is True
    assert result.status == IngestionPipelineStatus.INGESTED_WITH_REVIEW
    assert result.ingested is True
    assert runtime.calls[0]["metadata"]["quality_decision"] == "review"
    assert "very_short_content" in runtime.calls[0]["metadata"]["quality_review_reasons"]


def test_pipeline_supports_legacy_four_argument_runtime(tmp_path: Path):
    path = tmp_path / "legacy.txt"
    path.write_text("This legacy runtime document is long enough to be accepted.", encoding="utf-8")
    runtime = LegacyRuntime()

    result = DocumentIngestionPipeline(runtime).ingest_file(path)

    assert result.ok is True
    assert result.status == IngestionPipelineStatus.INGESTED_WITH_REVIEW
    assert len(runtime.calls) == 1


def test_pipeline_reports_runtime_not_ok_as_ingestion_failed(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("This document contains enough searchable content for ingestion.", encoding="utf-8")
    runtime = RecordingRuntime(ok=False)

    result = DocumentIngestionPipeline(runtime).ingest_file(path)

    assert result.ok is False
    assert result.status == IngestionPipelineStatus.INGESTION_FAILED
    assert result.ingested is False
    assert result.errors == ("store_failed",)


def test_pipeline_catches_runtime_exception(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("This document contains enough searchable content for ingestion.", encoding="utf-8")

    result = DocumentIngestionPipeline(FailingRuntime()).ingest_file(path)

    assert result.ok is False
    assert result.status == IngestionPipelineStatus.INGESTION_FAILED
    assert result.errors == ("ingestion_exception:database_down",)
