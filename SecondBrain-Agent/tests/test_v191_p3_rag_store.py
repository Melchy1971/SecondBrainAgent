from __future__ import annotations

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_rag_store import PgVectorRagStore, SQLiteRagStore, create_rag_store, store_backend_from_config


def test_sqlite_store_status_empty_when_db_missing(tmp_path):
    store = SQLiteRagStore(tmp_path / "missing.sqlite3")

    status = store.status()

    assert status["schema"] == "secondbrain.p3_rag_store.v1"
    assert status["backend"] == "sqlite"
    assert status["ok"] is True
    assert status["documents"] == 0
    assert status["chunks"] == 0
    assert status["vectors"] == 0


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


def test_create_rag_store_defaults_to_sqlite(tmp_path):
    store = create_rag_store(tmp_path)

    assert store.backend == "sqlite"
    assert store_backend_from_config(tmp_path) == "sqlite"


def test_create_rag_store_uses_pgvector_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")

    store = create_rag_store(tmp_path)
    status = store.status()

    assert isinstance(store, PgVectorRagStore)
    assert store_backend_from_config(tmp_path) == "pgvector"
    assert status["backend"] == "pgvector"
    assert status["ok"] is True
    assert status["config"]["dsn"] == "postgresql://user:***@db:5432/app"
    assert "sql_preview" in status


def test_pgvector_store_methods_are_explicitly_not_implemented(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    store = create_rag_store(tmp_path)

    assert store.sources()["status"] == "not_implemented"
    assert store.vector_search([0.1, 0.2])["error"] == "pgvector_vector_search_not_implemented_yet"


def test_p3_rag_store_status_launcher_sqlite(tmp_path, capsys):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="CLI")

    rc = main(["--project-root", str(tmp_path), "p3-rag-store-status"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "secondbrain.p3_rag_store.v1" in captured
    assert '"backend": "sqlite"' in captured


def test_p3_rag_store_status_launcher_pgvector(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")

    rc = main(["--project-root", str(tmp_path), "p3-rag-store-status"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert '"backend": "pgvector"' in captured
    assert "postgresql://user:***@db:5432/app" in captured


def test_p3_rag_store_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p3-rag-store-status"] == "core"
    assert ModuleRegistry().resolve_command("p3-rag-store-status").key == "core"
