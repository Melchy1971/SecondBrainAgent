from __future__ import annotations

from pathlib import Path

from secondbrain.p1_embeddings import deterministic_embedding
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import audit_vector_provider


class FakeProductionProvider:
    name = "fake-production-provider"
    dimensions = 16

    def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimensions)

    def status(self) -> dict:
        return {"ok": True, "provider": self.name, "dimensions": self.dimensions, "semantic": True, "production_ready": True, "fallback_used": False}


class SnapshotStore:
    backend = "snapshot-test-store"

    def validation_snapshot(self) -> dict:
        return {
            "ok": True,
            "status": "pass",
            "backend": self.backend,
            "chunks": [
                {"id": "chk_1", "token_json": '["jarvis"]'},
                {"id": "chk_2", "token_json": '["rag"]'},
            ],
            "embeddings": [
                {"chunk_id": "chk_1", "provider": "local-deterministic", "dimensions": 64, "vector_json": "[0.1]"},
                {"chunk_id": "chk_orphan", "provider": "other-provider", "dimensions": 64, "vector_json": "[0.2]"},
            ],
        }


class RuntimeWithSnapshotStore:
    db_path = Path("/path/that/must/not/be/read.sqlite3")
    reports_dir = Path("/tmp")
    rag_store = SnapshotStore()
    embedding_provider = FakeProductionProvider()


def test_vector_provider_guard_uses_active_rag_store_snapshot_not_sqlite(tmp_path):
    runtime = RuntimeWithSnapshotStore()

    audit = audit_vector_provider(runtime)

    assert audit["schema"] == "secondbrain.p1_vector_provider_guard.v1"
    assert audit["store_backend"] == "snapshot-test-store"
    assert audit["ok"] is False
    assert audit["stale_vectors"] == 2
    assert audit["missing_vectors"] == 1
    assert audit["orphan_vectors"] == 1
    assert set(audit["blockers"]) == {"stale_vector_provider", "missing_vectors", "orphan_vectors"}


def test_vector_provider_guard_report_uses_v2_schema(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")

    audit = audit_vector_provider(rt, write_report=True)

    assert audit["schema"] == "secondbrain.p1_vector_provider_guard.v1"
    assert audit["store_backend"] == "sqlite"
    assert audit["ok"] is True
    assert (tmp_path / "runtime" / "reports" / "p1_vector_provider_guard_latest.json").exists()
