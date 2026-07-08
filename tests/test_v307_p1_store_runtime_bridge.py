from __future__ import annotations

import os
from pathlib import Path

from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_rag_store import create_rag_store


def test_p1_runtime_uses_configured_rag_store_backend(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)

    assert runtime.rag_store.backend == "sqlite"
    assert runtime.status()["store"]["backend"] == "sqlite"


def test_p1_runtime_validation_is_store_backed(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_ENABLED", raising=False)
    runtime = P1RagRuntime(tmp_path)
    ingested = runtime.ingest_text("Jarvis nutzt RAG Quellen mit Zitaten.", source="unit://store-backed")

    assert ingested["ok"] is True
    validation = runtime.validate_index()
    assert validation["ok"] is True
    assert validation["documents"] == 1
    assert validation["chunks"] >= 1


def test_create_rag_store_selects_pgvector_when_enabled(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@example.org:5432/db")

    store = create_rag_store(tmp_path)

    assert store.backend == "pgvector"
    status = store.status()
    assert status["backend"] == "pgvector"
    assert status["dsn"] == "postgresql://user:***@example.org:5432/db"
