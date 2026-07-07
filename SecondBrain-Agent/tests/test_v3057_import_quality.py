from __future__ import annotations

import inspect
import json
import sqlite3

from secondbrain.importing import ImportCenterService, StreamingImportService
from secondbrain.importing.quality import detect_language
from secondbrain.native.streaming_import_panel import StreamingImportFrame


def _quality(service: StreamingImportService) -> dict:
    with sqlite3.connect(service.db_path) as connection:
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents ORDER BY created_at DESC LIMIT 1").fetchone()[0])
    return metadata["knowledge_quality"]


def test_duplicate_detection_is_visible_without_new_storage(tmp_path):
    first, duplicate = tmp_path / "one.txt", tmp_path / "two.txt"
    first.write_text("identical document content", encoding="utf-8")
    duplicate.write_text("identical document content", encoding="utf-8")
    service = StreamingImportService(tmp_path)
    service.import_document(first)
    skipped = service.import_document(duplicate)
    rows = ImportCenterService(tmp_path, engine=service).duplicates()
    assert skipped.skipped_documents == 1
    assert rows[0]["type"] == "duplicate"
    assert rows[0]["duplicate_document_id"]


def test_near_duplicate_detection_uses_quality_metadata(tmp_path):
    common = " ".join(f"term{index:02d}" for index in range(30))
    first, second = tmp_path / "first.txt", tmp_path / "second.txt"
    first.write_text(common + " original", encoding="utf-8")
    second.write_text(common + " revised", encoding="utf-8")
    service = StreamingImportService(tmp_path)
    service.import_document(first); service.scheduler.pool.run_until_idle(timeout=10)
    service.import_document(second); service.scheduler.pool.run_until_idle(timeout=10)
    duplicates = ImportCenterService(tmp_path, engine=service).duplicates()
    assert any(row["type"] == "near_duplicate" and row["similarity"] >= 0.82 for row in duplicates)


def test_language_classification_pii_secret_and_quality_score(tmp_path):
    source = tmp_path / "classified.txt"
    source.write_text(
        "Das Projekt enthält eine Roadmap und einen Sprint. Kontakt: max@example.com. "
        "api_key=supersecretvalue123 Architektur Wissen Entscheidung " * 20,
        encoding="utf-8",
    )
    service = StreamingImportService(tmp_path)
    service.import_document(source, source="docs")
    service.scheduler.pool.run_until_idle(timeout=10)
    quality = _quality(service)
    assert quality["language"] == "de"
    assert quality["classification"] == "project"
    assert quality["pii_detected"] is True
    assert quality["secret_detected"] is True
    assert 0 <= quality["knowledge_quality_score"] <= 100
    assert 0 <= quality["confidence_score"] <= 1
    assert {"chunk_quality", "embedding_quality", "ocr_quality", "parser_quality", "source_trust"} <= quality.keys()


def test_quality_dashboard_and_import_warnings_project_document_metadata(tmp_path):
    source = tmp_path / "weak.txt"
    source.write_text("kurz", encoding="utf-8")
    service = StreamingImportService(tmp_path)
    service.import_document(source)
    service.scheduler.pool.run_until_idle(timeout=10)
    center = ImportCenterService(tmp_path, engine=service)
    dashboard = center.quality_dashboard()
    assert dashboard["documents"] == 1
    assert 0 <= dashboard["average_score"] <= 100
    assert center.import_warnings()


def test_language_detection_is_deterministic():
    assert detect_language("This is the source and this is the document for the project.")[0] == "en"
    assert detect_language("Das ist eine Quelle und das ist ein Dokument für das Projekt.")[0] == "de"


def test_native_gui_contains_quality_areas():
    source = inspect.getsource(StreamingImportFrame)
    assert "Quality Dashboard" in source
    assert "Import Warnings" in source
    assert "Duplicate Viewer" in source
