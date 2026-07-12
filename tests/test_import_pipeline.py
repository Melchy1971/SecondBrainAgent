"""Tests der einheitlichen Import-Pipeline.

Indexer und Klassifikator sind injizierbar; die Tests laufen ohne Provider.
"""

from __future__ import annotations

from pathlib import Path

from secondbrain.import_pipeline import (
    ImportHistory, ImportStatus, UnifiedImportPipeline,
)


def make_pipeline(tmp_path: Path, *, indexer=None, failing_indexer: bool = False,
                  classifier=None) -> UnifiedImportPipeline:
    calls: list[dict] = []

    def ok_indexer(text: str, metadata: dict) -> dict:
        calls.append(metadata)
        return {"ok": True, "chunks": 1}

    def bad_indexer(text: str, metadata: dict) -> dict:
        raise RuntimeError("provider down")

    pipeline = UnifiedImportPipeline(
        tmp_path,
        indexer=indexer or (bad_indexer if failing_indexer else ok_indexer),
        classifier=classifier or (lambda text: {
            "document_type": "wissen",
            "tags": [],
            "confidence": 0.9,
            "needs_review": False,
            "sensitive": False,
            "pii": {"findings": [], "markers": []},
        }),
    )
    pipeline._test_index_calls = calls  # type: ignore[attr-defined]
    return pipeline


# --- Happy Path -----------------------------------------------------------------

def test_local_file_reaches_indexed_with_full_stage_history(tmp_path: Path):
    doc = tmp_path / "notiz.txt"
    doc.write_text("Projekt Telekom: nächster Schritt Backlog pflegen. " * 20, encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    job = pipeline.submit_file(doc)
    assert job.status == ImportStatus.QUEUED
    job = pipeline.process(job.job_id)
    assert job.status == ImportStatus.INDEXED
    stages = [s["stage"] for s in job.stage_history]
    assert stages == ["queued", "parsing", "classified", "chunked", "embedded", "indexed"]
    assert job.chunk_count >= 1
    assert job.document_type != ""


def test_connector_text_uses_same_path_as_local(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    job = pipeline.submit_text(
        "Rechnung 4711 über 99 EUR", source_ref="m365://mail/4711",
        connector="m365", title="Rechnung 4711")
    assert job.source_kind == "connector"
    assert job.sync_id.startswith("sync_")
    job = pipeline.process(job.job_id)
    assert job.status == ImportStatus.INDEXED
    assert [s["stage"] for s in job.stage_history][:2] == ["queued", "parsing"]
    assert "text" not in job.lineage  # Inline-Text wird nach Verarbeitung entfernt
    assert job.lineage["connector"] == "m365"


def test_incremental_indexing_one_call_per_document(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    for name in ("a", "b", "c"):
        doc = tmp_path / f"{name}.txt"
        doc.write_text(f"Inhalt {name} " * 30, encoding="utf-8")
        pipeline.submit_file(doc)
    result = pipeline.process_batch()
    assert result["indexed"] == 3
    assert len(pipeline._test_index_calls) == 3  # type: ignore[attr-defined]


# --- Duplicate Detection -----------------------------------------------------------

def test_duplicate_content_is_detected(tmp_path: Path):
    doc1 = tmp_path / "a.txt"
    doc2 = tmp_path / "b.txt"
    doc1.write_text("identischer Inhalt " * 10, encoding="utf-8")
    doc2.write_text("identischer Inhalt " * 10, encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    first = pipeline.submit_file(doc1)
    pipeline.process(first.job_id)
    second = pipeline.submit_file(doc2)
    assert second.status == ImportStatus.DUPLICATE
    assert second.duplicate_of == first.job_id


# --- Fehlerpfade ----------------------------------------------------------------------

def test_parser_error_does_not_block_queue_partial_failure(tmp_path: Path):
    good = tmp_path / "gut.txt"
    good.write_text("brauchbarer Inhalt " * 20, encoding="utf-8")
    bad = tmp_path / "kaputt.xyz_unbekannt"
    bad.write_text("x", encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    pipeline.submit_file(bad)
    pipeline.submit_file(good)
    result = pipeline.process_batch()
    assert result["processed"] == 2
    assert result["indexed"] == 1
    assert result["failed"] == 1


def test_failed_import_waits_for_review_without_retry_loop(tmp_path: Path):
    doc = tmp_path / "doc.txt"
    doc.write_text("Inhalt " * 30, encoding="utf-8")
    pipeline = make_pipeline(tmp_path, failing_indexer=True)
    job = pipeline.submit_file(doc)
    job = pipeline.process(job.job_id)
    review_id = job.review_id
    assert job.status == ImportStatus.FAILED_REVIEWABLE
    assert pipeline.retry(job.job_id).status == ImportStatus.FAILED_REVIEWABLE
    assert pipeline.process(job.job_id).status == ImportStatus.FAILED_REVIEWABLE
    assert len(pipeline.review_inbox.reviews.list()) == 1
    assert pipeline.store.get(job.job_id).review_id == review_id
    assert job.error_category == "unknown" or job.error_category  # kategorisiert
    assert job.attempts == 1


def test_approved_failed_import_can_retry_without_duplicate_review(tmp_path: Path):
    doc = tmp_path / "doc.txt"
    doc.write_text("Inhalt " * 30, encoding="utf-8")
    pipeline = make_pipeline(tmp_path, failing_indexer=True)
    job = pipeline.submit_file(doc)
    job.max_attempts = 1
    pipeline.store.upsert(job)
    job = pipeline.process(job.job_id)
    assert job.status == ImportStatus.FAILED_REVIEWABLE
    retried = pipeline.approve_review(job.review_id, "reviewer")
    assert retried.status == ImportStatus.FAILED_REVIEWABLE
    assert retried.review_status == "approved"
    assert len(pipeline.review_inbox.reviews.list()) == 1


# --- OCR ----------------------------------------------------------------------------------

class _OcrRegistry:
    class _Parsed:
        text = ""
        title = "scan.pdf"
        errors = ["pdf_text_empty_ocr_required"]

        class _Status:
            value = "ocr_required"
        status = _Status()

    def parse(self, path):
        return self._Parsed()


def test_ocr_required_is_own_wait_status(tmp_path: Path):
    doc = tmp_path / "scan.pdf"
    doc.write_bytes(b"%PDF-1.4 fake")
    pipeline = UnifiedImportPipeline(
        tmp_path, parser_registry=_OcrRegistry(),
        indexer=lambda t, m: {"ok": True})
    job = pipeline.submit_file(doc)
    job = pipeline.process(job.job_id)
    assert job.status == ImportStatus.OCR_REQUIRED
    assert job.ocr_required is True
    # nach OCR-Bereitstellung wieder einreihbar
    job = pipeline.retry(job.job_id)
    assert job.status == ImportStatus.QUEUED


# --- Lineage / Historie ---------------------------------------------------------------------

def test_lineage_is_recorded(tmp_path: Path):
    doc = tmp_path / "quelle.txt"
    doc.write_text("Inhalt " * 30, encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    job = pipeline.process(pipeline.submit_file(doc).job_id)
    assert job.lineage["source_kind"] == "local"
    assert job.lineage["content_hash"] == job.content_hash
    assert job.lineage["correlation_id"] == job.correlation_id


def test_history_snapshot_counts_and_jobs(tmp_path: Path):
    doc = tmp_path / "doc.txt"
    doc.write_text("Inhalt " * 30, encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    pipeline.process(pipeline.submit_file(doc).job_id)
    snapshot = ImportHistory(tmp_path).snapshot()
    assert snapshot["counts"] == {"indexed": 1}
    assert snapshot["jobs"][0]["status"] == "indexed"
    assert snapshot["jobs"][0]["stage_history"]


def test_import_actions_have_audit_trail(tmp_path: Path):
    from secondbrain.observability import AuditEventStore
    doc = tmp_path / "doc.txt"
    doc.write_text("Inhalt " * 30, encoding="utf-8")
    pipeline = make_pipeline(tmp_path)
    job = pipeline.process(pipeline.submit_file(doc).job_id)
    events = AuditEventStore(tmp_path).query(job_id=job.job_id)
    actions = {e["action"] for e in events}
    assert "import.queued" in actions
    assert "import.indexed" in actions
