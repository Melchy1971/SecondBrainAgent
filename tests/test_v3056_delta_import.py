from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

from secondbrain.importing import StreamingImportService
from secondbrain.p1_rag_runtime import fingerprint
from secondbrain.p3_pgvector_foundation import PgVectorConfig
from secondbrain.p3_rag_store import PgVectorRagStore, RagDocumentRecord


def _jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_delta_import_skips_unchanged_records_and_does_not_enqueue_pipeline(tmp_path):
    source = tmp_path / "delta.jsonl"
    _jsonl(source, [{"id": "c1", "title": "One", "content": "same"}])
    service = StreamingImportService(tmp_path, batch_size=1)
    first = service.import_file(source, source="chatgpt")
    first_jobs = len(service.queue.list_jobs(kind="chunk"))
    second = service.import_file(source, source="chatgpt")
    with sqlite3.connect(service.db_path) as connection:
        documents = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        actions = [row[0] for row in connection.execute("SELECT action FROM import_delta_entries ORDER BY id")]
    assert first.new_documents == 1
    assert second.imported_chats == 0 and second.skipped_documents == 1
    assert documents == 1 and actions == ["new", "unchanged"]
    assert len(service.queue.list_jobs(kind="chunk")) == first_jobs


def test_change_detection_updates_known_document_and_preserves_versions(tmp_path):
    source = tmp_path / "changed.jsonl"
    _jsonl(source, [{"id": "stable", "title": "Title", "content": "before"}])
    service = StreamingImportService(tmp_path, batch_size=1)
    service.import_file(source, source="claude")
    _jsonl(source, [{"id": "stable", "title": "Title", "content": "after"}])
    changed = service.import_file(source, source="claude")
    with sqlite3.connect(service.db_path) as connection:
        document = connection.execute("SELECT content_hash FROM documents").fetchone()[0]
        versions = connection.execute("SELECT version_number,content_hash FROM document_versions ORDER BY version_number").fetchall()
    assert changed.updated_documents == 1 and changed.new_documents == 0
    assert document != versions[0][1]
    assert [row[0] for row in versions] == [1, 2]


def test_hash_deduplication_skips_identical_document_from_another_path(tmp_path):
    first_path, second_path = tmp_path / "a.txt", tmp_path / "b.txt"
    first_path.write_text("identical", encoding="utf-8")
    second_path.write_text("identical", encoding="utf-8")
    service = StreamingImportService(tmp_path)
    service.import_document(first_path)
    duplicate = service.import_document(second_path)
    with sqlite3.connect(service.db_path) as connection:
        rows = connection.execute("SELECT content_hash FROM documents").fetchall()
        action = connection.execute("SELECT action FROM import_delta_entries ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert rows == [(fingerprint("identical"),)]
    assert duplicate.skipped_documents == 1 and action == "duplicate"


def test_auto_resume_reuses_interrupted_session(tmp_path):
    source = tmp_path / "resume.jsonl"
    _jsonl(source, [{"id": f"c{i}", "content": str(i)} for i in range(3)])
    service = StreamingImportService(tmp_path, batch_size=1)
    paused = service.import_file(source, stop_after_batches=1)
    interrupted = replace(paused, status="failed", control_state="running", error="interrupted")
    service.checkpoints.save(interrupted)
    resumed = service.import_file(source)
    assert resumed.session_id == paused.session_id
    assert resumed.status == "completed" and resumed.position == 3


def test_import_auto_retry_resumes_after_transient_batch_failure(tmp_path, monkeypatch):
    source = tmp_path / "retry.jsonl"
    _jsonl(source, [{"id": "c1", "content": "retry"}])
    service = StreamingImportService(tmp_path, batch_size=1)
    original = service.writer.write
    attempts = 0
    def flaky(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise sqlite3.OperationalError("database is temporarily busy")
        return original(*args, **kwargs)
    monkeypatch.setattr(service.writer, "write", flaky)
    session = service.import_file(source, auto_retry=2)
    assert attempts == 2
    assert session.status == "completed" and session.imported_chats == 1


def test_delta_pipeline_generates_all_existing_stages(tmp_path):
    source = tmp_path / "pipeline.jsonl"
    _jsonl(source, [{"id": "c1", "content": "pipeline content"}])
    service = StreamingImportService(tmp_path)
    service.import_file(source)
    service.scheduler.pool.run_until_idle(timeout=10)
    kinds = {job.kind for job in service.queue.list_jobs() if job.status == "success"}
    assert {"chunk", "embedding", "memory", "graph", "search"} <= kinds
    with sqlite3.connect(service.db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] > 0
        assert connection.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0] > 0
        metadata = json.loads(connection.execute("SELECT metadata_json FROM documents").fetchone()[0])
    assert {"memory_indexed_at", "graph_indexed_at", "search_indexed_at"} <= metadata.keys()
    assert "graph_entity_suggestions" in metadata
    assert "graph_relationship_suggestions" in metadata
    assert isinstance(metadata["graph_entity_suggestions"], list)
    assert isinstance(metadata["graph_relationship_suggestions"], list)


class _Copy:
    def __init__(self, owner): self.owner = owner
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def write_row(self, row): self.owner.rows.append(row)


class _Cursor:
    def __init__(self): self.sql = []; self.rows = []
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def execute(self, sql, _params=None): self.sql.append(str(sql))
    def copy(self, sql): self.sql.append(str(sql)); return _Copy(self)


class _Connection:
    def __init__(self): self.cursor_obj = _Cursor(); self.committed = False
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def cursor(self): return self.cursor_obj
    def commit(self): self.committed = True


def test_postgresql_bulk_path_uses_copy_and_upsert(monkeypatch):
    store = PgVectorRagStore(PgVectorConfig(True, "postgresql://user:pw@db/app"))
    connection = _Connection()
    monkeypatch.setattr(store, "_connect", lambda: connection)
    result = store.copy_documents([RagDocumentRecord("d1", "test", "Title", "hash", "now", {})])
    sql = "\n".join(connection.cursor_obj.sql).lower()
    assert result["ok"] is True and result["copied"] == 1
    assert "copy tmp_import_documents" in sql
    assert "on conflict(id) do update" in sql
    assert connection.committed is True
