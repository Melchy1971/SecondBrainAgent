from __future__ import annotations

from pathlib import Path

import pytest

from secondbrain.import_pipeline import ImportStatus, UnifiedImportPipeline
from secondbrain.native.approval import review_path


def _classification(
    *,
    confidence: float = 0.9,
    document_type: str = "vertrag",
    sensitive: bool = False,
    finding_type: str = "",
    finding_count: int = 0,
    markers: list[str] | None = None,
    conflict: bool = False,
) -> dict:
    findings = [{"type": finding_type, "count": finding_count}] if finding_type else []
    return {
        "document_type": document_type,
        "tags": ["test"],
        "confidence": confidence,
        "needs_review": confidence < 0.6,
        "sensitive": sensitive,
        "pii": {"findings": findings, "markers": markers or []},
        "classification_conflict": conflict,
    }


def _pipeline(tmp_path: Path, *, classifier=None, parser_registry=None):
    index_calls: list[dict] = []

    def indexer(text: str, metadata: dict) -> dict:
        index_calls.append({"text": text, "metadata": metadata})
        return {"ok": True}

    pipeline = UnifiedImportPipeline(
        tmp_path,
        classifier=classifier or (lambda text: _classification()),
        parser_registry=parser_registry,
        indexer=indexer,
    )
    return pipeline, index_calls


class _FailedParser:
    def __init__(self, error: str = "parser aborted") -> None:
        self.error = error

    def parse(self, path):
        error = self.error

        class Parsed:
            text = ""
            title = "broken.bin"
            errors = [error]
            metadata = {"parser": "failed-test-parser"}

            class Status:
                value = "failed"

            status = Status()

        return Parsed()


def _single_review(pipeline: UnifiedImportPipeline) -> dict:
    reviews = pipeline.review_inbox.reviews.list()
    assert len(reviews) == 1
    return reviews[0]


def test_parser_failure_creates_exactly_one_failed_import_review(tmp_path: Path) -> None:
    source = tmp_path / "broken.bin"
    source.write_bytes(b"broken")
    pipeline, index_calls = _pipeline(tmp_path, parser_registry=_FailedParser("corrupted parser input"))

    job = pipeline.process(pipeline.submit_file(source).job_id)
    retried = pipeline.retry(job.job_id)
    polled = pipeline.process(job.job_id)

    review = _single_review(pipeline)
    assert job.status == ImportStatus.FAILED_REVIEWABLE
    assert retried.review_id == polled.review_id == review["review_id"]
    assert review["category"] == "failed_import"
    assert review["metadata"]["error_code"] == "corrupted_file"
    assert index_calls == []


def test_sensitive_document_enters_review_and_blocks_automatic_forwarding(tmp_path: Path) -> None:
    pipeline, index_calls = _pipeline(
        tmp_path,
        classifier=lambda text: _classification(sensitive=True, finding_type="api_key", finding_count=1),
    )

    job = pipeline.process(pipeline.submit_text("credential material", source_ref="connector://secret").job_id)
    review = _single_review(pipeline)

    assert job.status == ImportStatus.REVIEW_REQUIRED
    assert review["category"] == "sensitive_document"
    assert job.memory_forwarding_blocked is True
    assert job.connector_forwarding_blocked is True
    assert job.indexing_blocked is True
    assert index_calls == []


def test_secret_signal_is_detected_even_when_classifier_does_not_flag_it(tmp_path: Path) -> None:
    secret = "sk-abcdefghijklmnopqrstuvwxyz123456"
    pipeline, index_calls = _pipeline(tmp_path, classifier=lambda text: _classification())

    job = pipeline.process(
        pipeline.submit_text(f"api_key={secret}", source_ref="doc://unflagged-secret").job_id
    )

    assert job.status == ImportStatus.REVIEW_REQUIRED
    assert job.review_category == "sensitive_document"
    assert secret not in review_path(tmp_path).read_text(encoding="utf-8")
    assert index_calls == []


def test_pii_threshold_and_confidential_classification_create_sensitive_review(tmp_path: Path) -> None:
    pipeline, _ = _pipeline(
        tmp_path,
        classifier=lambda text: _classification(
            sensitive=True,
            finding_type="email",
            finding_count=3,
        ),
    )
    job = pipeline.process(pipeline.submit_text("PII summary", source_ref="doc://pii").job_id)
    assert job.review_category == "sensitive_document"

    other_root = tmp_path / "confidential"
    confidential, _ = _pipeline(
        other_root,
        classifier=lambda text: _classification(sensitive=True, markers=["confidential"]),
    )
    other = confidential.process(confidential.submit_text("internal", source_ref="doc://confidential").job_id)
    assert other.review_category == "sensitive_document"


@pytest.mark.parametrize(
    "classification",
    [
        _classification(confidence=0.2),
        _classification(document_type=""),
        _classification(conflict=True),
    ],
)
def test_uncertain_classification_creates_review_without_losing_raw_import(
    tmp_path: Path,
    classification: dict,
) -> None:
    pipeline, index_calls = _pipeline(tmp_path, classifier=lambda text: classification)
    job = pipeline.process(pipeline.submit_text("raw imported text", source_ref="doc://uncertain").job_id)

    review = _single_review(pipeline)
    stored = pipeline.store.get(job.job_id)
    assert review["category"] == "low_confidence_classification"
    assert job.classification_blocked is True
    assert stored is not None and stored.lineage["text"] == "raw imported text"
    assert index_calls == []


def test_approve_continues_import_exactly_once(tmp_path: Path) -> None:
    classification_calls = 0

    def classifier(text: str) -> dict:
        nonlocal classification_calls
        classification_calls += 1
        return _classification(sensitive=True, finding_type="private_key", finding_count=1)

    pipeline, index_calls = _pipeline(
        tmp_path,
        classifier=classifier,
    )
    waiting = pipeline.process(pipeline.submit_text("private material", source_ref="doc://approve").job_id)

    completed = pipeline.approve_review(waiting.review_id, "reviewer", "approved")

    assert completed.status == ImportStatus.INDEXED
    assert completed.review_status == "approved"
    assert len(index_calls) == 1
    assert classification_calls == 1
    assert [stage["stage"] for stage in completed.stage_history].count("classified") == 1
    assert [stage["stage"] for stage in completed.stage_history].count("chunked") == 1
    assert pipeline.process(completed.job_id).status == ImportStatus.INDEXED
    assert len(index_calls) == 1


def test_approve_after_index_failure_retries_only_incomplete_stage(tmp_path: Path) -> None:
    calls = {"classification": 0, "chunking": 0, "indexing": 0}

    def classifier(text: str) -> dict:
        calls["classification"] += 1
        return _classification()

    def chunker(text: str) -> list[str]:
        calls["chunking"] += 1
        return [text]

    def indexer(text: str, metadata: dict) -> dict:
        calls["indexing"] += 1
        if calls["indexing"] == 1:
            raise RuntimeError("indexing failed")
        return {"ok": True}

    pipeline = UnifiedImportPipeline(
        tmp_path,
        classifier=classifier,
        chunker=chunker,
        indexer=indexer,
    )
    waiting = pipeline.process(
        pipeline.submit_text("document", source_ref="doc://resume-index").job_id
    )

    completed = pipeline.approve_review(waiting.review_id, "reviewer")

    assert completed.status == ImportStatus.INDEXED
    assert calls == {"classification": 1, "chunking": 1, "indexing": 2}


def test_reject_prevents_indexing_and_archives_inline_content(tmp_path: Path) -> None:
    pipeline, index_calls = _pipeline(tmp_path, classifier=lambda text: _classification(confidence=0.1))
    waiting = pipeline.process(pipeline.submit_text("raw content", source_ref="doc://reject").job_id)

    rejected = pipeline.reject_review(waiting.review_id, "reviewer", "not trusted")

    assert rejected.status == ImportStatus.REJECTED
    assert rejected.lineage.get("text") is None
    assert pipeline.process(rejected.job_id).status == ImportStatus.REJECTED
    assert index_calls == []


def test_defer_keeps_import_paused(tmp_path: Path) -> None:
    pipeline, index_calls = _pipeline(tmp_path, classifier=lambda text: _classification(confidence=0.1))
    waiting = pipeline.process(pipeline.submit_text("raw content", source_ref="doc://defer").job_id)

    deferred = pipeline.defer_review(
        waiting.review_id,
        "reviewer",
        until="2026-08-01T00:00:00Z",
        note="later",
    )

    assert deferred.status == ImportStatus.REVIEW_DEFERRED
    assert pipeline.process(deferred.job_id).status == ImportStatus.REVIEW_DEFERRED
    assert index_calls == []


def test_restart_observes_external_review_decision_and_resumes_once(tmp_path: Path) -> None:
    pipeline, index_calls = _pipeline(tmp_path, classifier=lambda text: _classification(confidence=0.1))
    waiting = pipeline.process(pipeline.submit_text("raw content", source_ref="doc://restart").job_id)
    pipeline.review_inbox.approve(waiting.review_id, "reviewer", "approved in inbox")

    restarted = UnifiedImportPipeline(
        tmp_path,
        classifier=lambda text: pytest.fail("completed classification must not run again"),
        indexer=lambda text, metadata: index_calls.append(metadata) or {"ok": True},
    )
    completed = restarted.process(waiting.job_id)

    assert completed.status == ImportStatus.INDEXED
    assert len(index_calls) == 1
    assert restarted.process(waiting.job_id).status == ImportStatus.INDEXED
    assert len(index_calls) == 1


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        ("unsupported file format", "unsupported_format"),
        ("OCR engine failed", "ocr_failed"),
    ],
)
def test_parser_failure_codes_are_preserved_as_sanitized_metadata(
    tmp_path: Path,
    error: str,
    expected_code: str,
) -> None:
    source = tmp_path / "document.bin"
    source.write_bytes(b"broken")
    pipeline, _ = _pipeline(tmp_path, parser_registry=_FailedParser(error))

    pipeline.process(pipeline.submit_file(source).job_id)

    review = _single_review(pipeline)
    assert review["metadata"]["error_code"] == expected_code


@pytest.mark.parametrize(
    ("chunker", "indexer", "expected_code", "resume_status"),
    [
        (
            lambda text: (_ for _ in ()).throw(RuntimeError("chunk worker failed")),
            lambda text, metadata: {"ok": True},
            "chunking_failed",
            ImportStatus.CLASSIFIED,
        ),
        (
            lambda text: [text],
            lambda text, metadata: (_ for _ in ()).throw(RuntimeError("embedding provider failed")),
            "embedding_failed",
            ImportStatus.CHUNKED,
        ),
    ],
)
def test_processing_failures_keep_exact_resume_stage(
    tmp_path: Path,
    chunker,
    indexer,
    expected_code: str,
    resume_status: str,
) -> None:
    pipeline = UnifiedImportPipeline(
        tmp_path,
        classifier=lambda text: _classification(),
        chunker=chunker,
        indexer=indexer,
    )

    job = pipeline.process(pipeline.submit_text("document", source_ref="doc://stage-failure").job_id)
    review = _single_review(pipeline)

    assert job.status == ImportStatus.FAILED_REVIEWABLE
    assert job.review_resume_status == resume_status
    assert review["metadata"]["error_code"] == expected_code


def test_review_metadata_and_audit_never_contain_document_or_secrets(tmp_path: Path) -> None:
    secret = "secret-value-123456789"
    source = tmp_path / "broken.bin"
    source.write_bytes(b"broken")
    pipeline, _ = _pipeline(tmp_path, parser_registry=_FailedParser(f"api_key={secret}"))
    waiting = pipeline.process(pipeline.submit_file(source).job_id)
    pipeline.reject_review(waiting.review_id, "reviewer", f"password={secret}")

    review = pipeline.review_inbox.reviews.get(waiting.review_id)
    metadata = review["metadata"]
    assert set(metadata) == {
        "import_job_id",
        "document_id",
        "source",
        "parser",
        "error_code",
        "confidence",
        "classification",
        "sanitized_error",
        "retry_allowed",
        "created_at",
    }
    queue_text = review_path(tmp_path).read_text(encoding="utf-8")
    audit_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "runtime" / "observability").rglob("*.json*")
        if path.is_file()
    )
    assert secret not in queue_text
    assert secret not in audit_text
    assert "document_content" not in metadata
