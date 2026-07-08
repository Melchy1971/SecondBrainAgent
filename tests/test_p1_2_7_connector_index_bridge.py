from datetime import datetime, timezone

from secondbrain.connectors.import_bridge import ConnectorImportJob, ImportJobStatus
from secondbrain.connectors.index_bridge import (
    ConnectorIndexBridge,
    ConnectorIndexStatus,
    InMemoryIndexDocumentSink,
)
from secondbrain.rag.indexing.change_detector import ChangeAction, DocumentSnapshot
from secondbrain.rag.indexing.reindex_service import InMemoryIndexRepository


def make_job(*, key="gmail:42", content_hash="h1", status=ImportJobStatus.IMPORTED, content="hello"):
    return ConnectorImportJob(
        job_id=f"job:{key}:{content_hash}",
        document_key=key,
        source="gmail",
        external_id="42",
        title="Mail 42",
        content=content,
        content_hash=content_hash,
        updated_at=datetime(2026, 6, 23, tzinfo=timezone.utc),
        uri="gmail://42",
        mime_type="text/plain",
        status=status,
    )


def test_imported_job_is_indexed_and_snapshot_is_stored():
    repo = InMemoryIndexRepository()
    sink = InMemoryIndexDocumentSink()
    bridge = ConnectorIndexBridge(repo, sink)

    plan = bridge.apply_jobs([make_job()])

    assert plan.summary() == {"total": 1, "reindex": 1, "delete": 0, "skip": 0}
    assert sink.indexed["gmail:42"].content == "hello"
    assert repo.snapshots["gmail:42"].content_hash == "h1"
    assert bridge.snapshot()["indexed"] == 1
    assert bridge.snapshot()["ok"] is True


def test_unchanged_content_is_skipped_without_reindex_side_effect():
    repo = InMemoryIndexRepository(snapshots={"gmail:42": DocumentSnapshot("gmail:42", "h1")})
    sink = InMemoryIndexDocumentSink()
    bridge = ConnectorIndexBridge(repo, sink)

    plan = bridge.apply_jobs([make_job(content_hash="h1")])

    assert plan.skipped[0].action == ChangeAction.SKIP
    assert sink.indexed == {}
    assert bridge.snapshot()["skipped"] == 1


def test_changed_content_reindexes_same_document_key():
    repo = InMemoryIndexRepository(snapshots={"gmail:42": DocumentSnapshot("gmail:42", "h1")})
    sink = InMemoryIndexDocumentSink()
    bridge = ConnectorIndexBridge(repo, sink)

    plan = bridge.apply_jobs([make_job(content_hash="h2", content="changed")])

    assert plan.to_reindex[0].reason == "content_changed"
    assert repo.snapshots["gmail:42"].content_hash == "h2"
    assert sink.indexed["gmail:42"].content == "changed"


def test_non_imported_jobs_are_skipped_before_index_plan():
    repo = InMemoryIndexRepository()
    sink = InMemoryIndexDocumentSink()
    bridge = ConnectorIndexBridge(repo, sink)

    plan = bridge.apply_jobs([make_job(status=ImportJobStatus.SKIPPED)])

    assert plan.summary() == {"total": 0, "reindex": 0, "delete": 0, "skip": 0}
    assert bridge.results[0].status == ConnectorIndexStatus.SKIPPED
    assert bridge.results[0].reason == "job_not_imported"


def test_index_failure_is_isolated_when_fail_fast_is_false():
    repo = InMemoryIndexRepository()
    sink = InMemoryIndexDocumentSink(fail_on_index={"gmail:42"})
    bridge = ConnectorIndexBridge(repo, sink, fail_fast=False)

    plan = bridge.apply_jobs([make_job()])

    assert plan.summary()["reindex"] == 1
    snapshot = bridge.snapshot()
    assert snapshot["failed"] == 1
    assert snapshot["ok"] is False


def test_deleted_connector_document_removes_repository_and_sink_state():
    repo = InMemoryIndexRepository(snapshots={"gmail:42": DocumentSnapshot("gmail:42", "h1")})
    sink = InMemoryIndexDocumentSink(indexed={"gmail:42": make_job()})
    bridge = ConnectorIndexBridge(repo, sink)

    results = bridge.apply_deleted(["gmail:42"])

    assert results[0].status == ConnectorIndexStatus.DELETED
    assert "gmail:42" not in repo.snapshots
    assert sink.deleted == ["gmail:42"]
    assert bridge.snapshot()["deleted"] == 1
