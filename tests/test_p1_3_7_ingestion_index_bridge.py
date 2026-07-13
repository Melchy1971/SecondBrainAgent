from pathlib import Path

from secondbrain.document_understanding.ingestion_pipeline import DocumentIngestionPipeline, IngestionPipelineStatus
from secondbrain.document_understanding.index_bridge import (
    IngestionIndexBridge,
    IngestionIndexStatus,
    InMemoryIngestionIndexSink,
)
from secondbrain.rag.indexing.change_detector import ChangeAction, DocumentSnapshot
from secondbrain.rag.indexing.reindex_service import InMemoryIndexRepository


class Runtime:
    def __init__(self, *, ok=True, document_id="doc:1"):
        self.ok = ok
        self.document_id = document_id
        self.calls = []

    def ingest_text(self, title, text, source_path="manual", mime_type="text/plain", metadata=None):
        self.calls.append((title, text, source_path, mime_type, metadata or {}))
        return {"ok": self.ok, "document_id": self.document_id}


def write_file(tmp_path: Path, name="doc.txt", text="Enough searchable text for the ingestion quality gate.") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def make_ingested_result(tmp_path: Path, *, document_id="doc:1", text="Enough searchable text for the ingestion quality gate."):
    runtime = Runtime(document_id=document_id)
    pipeline = DocumentIngestionPipeline(runtime)
    result = pipeline.ingest_file(write_file(tmp_path, text=text))
    assert result.status in {IngestionPipelineStatus.INGESTED, IngestionPipelineStatus.INGESTED_WITH_REVIEW}
    return result


def test_successful_ingestion_result_is_indexed_and_snapshot_is_stored(tmp_path):
    result = make_ingested_result(tmp_path, document_id="doc:1")
    repo = InMemoryIndexRepository()
    sink = InMemoryIngestionIndexSink()
    bridge = IngestionIndexBridge(repo, sink)

    plan = bridge.apply_results([result])

    assert plan.summary() == {"total": 1, "reindex": 1, "delete": 0, "skip": 0}
    assert sink.indexed["doc:1"].content.startswith("Enough searchable text")
    assert repo.snapshots["doc:1"].metadata["title"] == "doc.txt"
    assert bridge.snapshot()["indexed"] == 1
    assert bridge.snapshot()["ok"] is True


def test_unchanged_ingested_document_is_skipped_without_index_side_effect(tmp_path):
    result = make_ingested_result(tmp_path, document_id="doc:1")
    existing = DocumentSnapshot("doc:1", result.orchestration.parsed.metadata.get("content_hash") or sink_hash(result))
    repo = InMemoryIndexRepository(snapshots={"doc:1": existing})
    sink = InMemoryIngestionIndexSink()
    bridge = IngestionIndexBridge(repo, sink)

    plan = bridge.apply_results([result])

    assert plan.skipped[0].action == ChangeAction.SKIP
    assert sink.indexed == {}
    assert bridge.snapshot()["skipped"] == 1


def test_changed_ingested_document_reindexes_same_document_id(tmp_path):
    result = make_ingested_result(tmp_path, document_id="doc:1", text="Changed searchable text for indexing again.")
    repo = InMemoryIndexRepository(snapshots={"doc:1": DocumentSnapshot("doc:1", "old")})
    sink = InMemoryIngestionIndexSink()
    bridge = IngestionIndexBridge(repo, sink)

    plan = bridge.apply_results([result])

    assert plan.to_reindex[0].reason == "content_changed"
    assert repo.snapshots["doc:1"].content_hash != "old"
    assert sink.indexed["doc:1"].content.startswith("Changed searchable")


def test_rejected_ingestion_result_is_skipped_before_reindex(tmp_path):
    runtime = Runtime(document_id="doc:reject")
    pipeline = DocumentIngestionPipeline(runtime)
    result = pipeline.ingest_file(write_file(tmp_path, text="x"))
    assert result.status == IngestionPipelineStatus.REJECTED
    repo = InMemoryIndexRepository()
    sink = InMemoryIngestionIndexSink()
    bridge = IngestionIndexBridge(repo, sink)

    plan = bridge.apply_results([result])

    assert plan.summary() == {"total": 0, "reindex": 0, "delete": 0, "skip": 0}
    assert sink.indexed == {}
    assert bridge.results[0].status == IngestionIndexStatus.SKIPPED
    assert bridge.results[0].reason == "ingestion_not_successful"


def test_index_failure_is_isolated_when_fail_fast_is_false(tmp_path):
    result = make_ingested_result(tmp_path, document_id="doc:1")
    repo = InMemoryIndexRepository()
    sink = InMemoryIngestionIndexSink(fail_on_index={"doc:1"})
    bridge = IngestionIndexBridge(repo, sink, fail_fast=False)

    plan = bridge.apply_results([result])

    assert plan.summary()["reindex"] == 1
    snapshot = bridge.snapshot()
    assert snapshot["failed"] == 1
    assert snapshot["ok"] is False


def test_deleted_document_removes_repository_and_sink_state():
    repo = InMemoryIndexRepository(snapshots={"doc:1": DocumentSnapshot("doc:1", "h1")})
    sink = InMemoryIngestionIndexSink()
    bridge = IngestionIndexBridge(repo, sink)

    results = bridge.apply_deleted(["doc:1"])

    assert results[0].status == IngestionIndexStatus.DELETED
    assert "doc:1" not in repo.snapshots
    assert sink.deleted == ["doc:1"]
    assert bridge.snapshot()["deleted"] == 1


def sink_hash(result):
    from secondbrain.rag.indexing.change_detector import hash_document_text

    return hash_document_text(result.orchestration.parsed.text)
