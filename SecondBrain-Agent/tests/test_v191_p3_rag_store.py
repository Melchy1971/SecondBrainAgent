from __future__ import annotations

import sys

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_embeddings import deterministic_embedding
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_rag_store import PgVectorRagStore, RagChunkRecord, RagDocumentRecord, RagVectorRecord, SQLiteRagStore, create_rag_store, store_backend_from_config


class _FakeCursor:
    def __init__(self):
        self.queries: list[tuple[str, tuple | None]] = []
        self._last_query = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self._last_query = str(sql)
        self.queries.append((str(sql), params))

    def fetchone(self):
        if "count(*) from secondbrain.p1_documents" in self._last_query:
            return [1]
        if "count(*) from secondbrain.p1_chunks" in self._last_query:
            return [1]
        if "count(*) from secondbrain.p1_chunk_embeddings" in self._last_query:
            return [1]
        return [1]

    def fetchall(self):
        if "group by provider" in self._last_query:
            return [("openai", 1536, 1)]
        if "left join" in self._last_query and "p1_chunks" in self._last_query:
            return [("doc1", "unit", "Doc", "hash1", "2026-01-01T00:00:00Z", {"kind": "test"}, 1)]
        if "embedding <=>" in self._last_query:
            return [("chk1", "doc1", "unit", "Doc", "Jarvis RAG Quellen", "openai", 3, 0.91)]
        return []


class _FakeConnection:
    def __init__(self):
        self.cursor_obj = _FakeCursor()
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1


class _FakePsycopg:
    def __init__(self):
        self.connections: list[_FakeConnection] = []

    def connect(self, dsn, connect_timeout=5):
        assert dsn.startswith("postgresql://")
        assert connect_timeout == 5
        conn = _FakeConnection()
        self.connections.append(conn)
        return conn


def _enable_pgvector(monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")


def test_sqlite_store_status_empty_when_db_missing(tmp_path):
    store = SQLiteRagStore(tmp_path / "missing.sqlite3")

    status = store.status()

    assert status["schema"] == "secondbrain.p3_rag_store.v3"
    assert status["backend"] == "sqlite"
    assert status["ok"] is True
    assert status["documents"] == 0
    assert status["chunks"] == 0
    assert status["vectors"] == 0
    assert "upsert_document" in status["capabilities"]


def test_sqlite_store_reads_existing_p1_rag_index(tmp_path):
    rt = P1RagRuntime(tmp_path)
    ingest = rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Store")
    store = SQLiteRagStore(rt.db_path)

    status = store.status()
    sources = store.sources()
    vector = store.vector_search(rt.embedding_provider.embed("Jarvis Quellen"), limit=3)

    assert status["ok"] is True
    assert status["documents"] == 1
    assert status["chunks"] == ingest["chunks"]
    assert status["vectors"] == ingest["chunks"]
    assert status["providers"][0]["provider"] == "local-deterministic"
    assert sources["sources"][0]["title"] == "Store"
    assert vector["hit_count"] >= 1
    assert vector["hits"][0]["provider"] == "local-deterministic"


def test_sqlite_store_write_contract_roundtrip(tmp_path):
    store = SQLiteRagStore(tmp_path / "rag.sqlite3")
    doc = RagDocumentRecord("doc1", "unit", "Doc", "hash1", "2026-01-01T00:00:00Z", {"kind": "test"})
    chunk = RagChunkRecord("chk1", "doc1", 0, "Jarvis RAG Quellen", 0, 18, ["jarvis", "rag", "quellen"], 3, "2026-01-01T00:00:00Z")
    vector = RagVectorRecord("chk1", "unit-provider", 8, deterministic_embedding(chunk.text, 8), "2026-01-01T00:00:00Z")

    assert store.upsert_document(doc)["ok"] is True
    assert store.upsert_chunks([chunk])["chunks"] == 1
    assert store.upsert_vectors([vector])["vectors"] == 1

    status = store.status()
    hits = store.vector_search(deterministic_embedding("Jarvis Quellen", 8), provider="unit-provider")

    assert status["documents"] == 1
    assert status["chunks"] == 1
    assert status["vectors"] == 1
    assert hits["hit_count"] == 1
    assert hits["hits"][0]["chunk_id"] == "chk1"


def test_create_rag_store_defaults_to_sqlite(tmp_path):
    store = create_rag_store(tmp_path)

    assert store.backend == "sqlite"
    assert store_backend_from_config(tmp_path) == "sqlite"


def test_create_rag_store_uses_pgvector_when_enabled(tmp_path, monkeypatch):
    _enable_pgvector(monkeypatch)

    store = create_rag_store(tmp_path)
    status = store.status()

    assert isinstance(store, PgVectorRagStore)
    assert store_backend_from_config(tmp_path) == "pgvector"
    assert status["backend"] == "pgvector"
    assert status["ok"] is True
    assert status["config"]["dsn"] == "postgresql://user:***@db:5432/app"
    assert "sql_preview" in status
    assert "live_vector_search" in status["capabilities"]


def test_pgvector_store_blocks_live_methods_without_psycopg(tmp_path, monkeypatch):
    _enable_pgvector(monkeypatch)
    monkeypatch.setitem(sys.modules, "psycopg", None)
    store = create_rag_store(tmp_path)
    doc = RagDocumentRecord("doc1", "unit", "Doc", "hash1", "2026-01-01T00:00:00Z", {"kind": "test"})

    result = store.upsert_document(doc)

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["error"] == "psycopg_missing"
    assert "pw" not in result["dsn"]


def test_pgvector_store_live_write_and_search_with_fake_psycopg(tmp_path, monkeypatch):
    fake = _FakePsycopg()
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    _enable_pgvector(monkeypatch)
    store = create_rag_store(tmp_path)
    doc = RagDocumentRecord("doc1", "unit", "Doc", "hash1", "2026-01-01T00:00:00Z", {"kind": "test"})
    chunk = RagChunkRecord("chk1", "doc1", 0, "Jarvis RAG Quellen", 0, 18, ["jarvis", "rag", "quellen"], 3, "2026-01-01T00:00:00Z")
    vector = RagVectorRecord("chk1", "openai", 3, [0.1, 0.2, 0.3], "2026-01-01T00:00:00Z")

    doc_result = store.upsert_document(doc)
    chunk_result = store.upsert_chunks([chunk])
    vector_result = store.upsert_vectors([vector])
    sources = store.sources()
    hits = store.vector_search([0.1, 0.2, 0.3], provider="openai", limit=3)

    assert doc_result["ok"] is True
    assert chunk_result["chunks"] == 1
    assert vector_result["vectors"] == 1
    assert sources["sources"][0]["title"] == "Doc"
    assert hits["hit_count"] == 1
    assert hits["hits"][0]["chunk_id"] == "chk1"
    assert any("p1_documents" in query for conn in fake.connections for query, _ in conn.cursor_obj.queries)
    assert any("p1_chunk_embeddings" in query for conn in fake.connections for query, _ in conn.cursor_obj.queries)


def test_pgvector_store_status_reads_live_counts_with_fake_psycopg(tmp_path, monkeypatch):
    fake = _FakePsycopg()
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    _enable_pgvector(monkeypatch)
    store = create_rag_store(tmp_path)

    status = store.status()

    assert status["ok"] is True
    assert status["live"]["ok"] is True
    assert status["documents"] == 1
    assert status["providers"][0]["provider"] == "openai"


def test_p3_rag_store_status_launcher_sqlite(tmp_path, capsys):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="CLI")

    rc = main(["--project-root", str(tmp_path), "p3-rag-store-status"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "secondbrain.p3_rag_store.v3" in captured
    assert '"backend": "sqlite"' in captured


def test_p3_rag_store_status_launcher_pgvector(tmp_path, capsys, monkeypatch):
    _enable_pgvector(monkeypatch)

    rc = main(["--project-root", str(tmp_path), "p3-rag-store-status"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert '"backend": "pgvector"' in captured
    assert "postgresql://user:***@db:5432/app" in captured


def test_p3_rag_store_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p3-rag-store-status"] == "core"
    assert ModuleRegistry().resolve_command("p3-rag-store-status").key == "core"
