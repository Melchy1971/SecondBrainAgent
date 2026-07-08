from __future__ import annotations

import sys
from pathlib import Path

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_migration import migrate_sqlite_to_selected_store
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_pgvector_foundation import load_pgvector_config, pgvector_live_check


class _MissingVectorCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.sql = sql

    def fetchone(self):
        if "version()" in self.sql:
            return ["PostgreSQL fake"]
        if "pg_extension" in self.sql:
            return None
        return [0]


class _MissingVectorConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return _MissingVectorCursor()


class _MissingVectorPsycopg:
    def connect(self, *args, **kwargs):
        return _MissingVectorConn()


def test_vector_search_uses_rag_store_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)
    runtime.ingest_text("Jarvis nutzt RAG Quellen und robuste Store Suche.", source="unit://vector-store")

    called = {"n": 0}
    original = runtime.rag_store.vector_search

    def spy(*args, **kwargs):
        called["n"] += 1
        return original(*args, **kwargs)

    runtime.rag_store.vector_search = spy  # type: ignore[method-assign]
    result = runtime.vector_search("Jarvis Quellen", limit=3)

    assert result["ok"] is True
    assert called["n"] == 1
    assert result["store"]["backend"] == "sqlite"


def test_sqlite_to_pgvector_migration_blocks_non_pgvector_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)
    runtime.ingest_text("Migration Quelle", source="unit://migration")

    result = migrate_sqlite_to_selected_store(tmp_path)

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blockers"][0]["code"] == "target_store_not_pgvector"


def test_sqlite_to_pgvector_migration_dry_run_allows_non_pgvector_for_tests(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)
    runtime.ingest_text("Migration Dry Run Quelle", source="unit://migration-dry")

    result = migrate_sqlite_to_selected_store(tmp_path, require_pgvector=False, dry_run=True, write_report=True)

    assert result["ok"] is True
    assert result["status"] == "dry_run"
    assert result["plan"]["documents"] == 1
    assert result["plan"]["chunks"] >= 1
    assert result["report"]["bytes"] > 0


def test_pgvector_live_check_blocks_when_extension_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setitem(sys.modules, "psycopg", _MissingVectorPsycopg())
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    config = load_pgvector_config(tmp_path)

    live = pgvector_live_check(config)

    assert live["ok"] is False
    assert live["status"] == "blocked"
    assert live["error"] == "pgvector_extension_missing"


def test_p1_migration_launcher_and_command_index(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)
    runtime.ingest_text("Launcher Migration Quelle", source="unit://migration-launcher")

    rc = main(["--project-root", str(tmp_path), "p1-rag-migrate-postgres", "--allow-non-pgvector", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "secondbrain.p1_rag.sqlite_to_pgvector.v1" in captured
    assert ModuleRegistry().resolve_command("p1-rag-migrate-postgres").key == "core"
