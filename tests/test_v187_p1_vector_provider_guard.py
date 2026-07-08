from __future__ import annotations

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_embeddings import deterministic_embedding
from secondbrain.p1_production_gate import production_gate_with_golden
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import audit_vector_provider


class FakeProductionProvider:
    name = "fake-production-provider"
    dimensions = 16

    def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimensions)

    def status(self) -> dict:
        return {
            "ok": True,
            "provider": self.name,
            "dimensions": self.dimensions,
            "network": False,
            "semantic": True,
            "fallback_used": False,
            "production_ready": True,
        }


def test_vector_provider_guard_passes_for_current_provider(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")

    audit = audit_vector_provider(rt, write_report=True)

    assert audit["schema"] == "secondbrain.p1_vector_provider_guard.v1"
    assert audit["ok"] is True
    assert audit["stale_vectors"] == 0
    assert audit["missing_vectors"] == 0
    assert audit["providers"][0]["provider"].startswith("local-deterministic:")
    assert (tmp_path / "runtime" / "reports" / "p1_vector_provider_guard_latest.json").exists()


def test_vector_provider_guard_blocks_after_provider_change_until_reindex(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")
    rt.embedding_provider = FakeProductionProvider()

    stale = audit_vector_provider(rt)

    assert stale["ok"] is False
    assert stale["status"] == "blocked"
    assert stale["current_provider"].startswith("fake-production-provider:")
    assert stale["stale_vectors"] >= 1
    assert "stale_vector_provider" in stale["blockers"]
    assert "p1-rag-reindex" in stale["remediation"]

    rt.reindex_vectors(write_report=True)
    repaired = audit_vector_provider(rt)

    assert repaired["ok"] is True
    assert repaired["stale_vectors"] == 0
    assert repaired["providers"][0]["provider"].startswith("fake-production-provider:")


def test_production_gate_contains_vector_provider_audit(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")
    rt.embedding_provider = FakeProductionProvider()

    payload = production_gate_with_golden(rt, tmp_path)

    assert payload["ok"] is False
    assert "vector_provider_guard" in payload
    assert payload["vector_provider_guard"]["ok"] is False
    assert any(check["name"] == "vector_provider_audit_passes" and check["ok"] is False for check in payload["checks"])


def test_vector_provider_audit_launcher_command(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen", "--source", "unit", "--title", "Seed"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-vector-provider-audit", "--write-report"]) == 0
    captured = capsys.readouterr().out

    assert "secondbrain.p1_vector_provider_guard.v1" in captured
    assert (tmp_path / "runtime" / "reports" / "p1_vector_provider_guard_latest.json").exists()


def test_vector_provider_audit_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p1-vector-provider-audit"] == "core"
    assert ModuleRegistry().resolve_command("p1-vector-provider-audit").key == "core"

class SameProviderDifferentDimensions:
    name = "local-deterministic"
    dimensions = 32

    def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimensions)

    def status(self) -> dict:
        return {
            "ok": True,
            "provider": self.name,
            "dimensions": self.dimensions,
            "network": False,
            "semantic": True,
            "fallback_used": False,
            "production_ready": True,
        }


def test_vector_provider_guard_blocks_same_provider_dimension_drift(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")
    rt.embedding_provider = SameProviderDifferentDimensions()

    drift = audit_vector_provider(rt)

    assert drift["ok"] is False
    assert drift["status"] == "blocked"
    assert drift["current_provider"].startswith("local-deterministic:")
    assert drift["dimension_mismatch_vectors"] >= 1
    assert "dimension_mismatch_vectors" in drift["blockers"]
    assert "provider/model/dimensions" in drift["remediation"]

    rt.reindex_vectors(write_report=True)
    repaired = audit_vector_provider(rt)

    assert repaired["ok"] is True
    assert repaired["dimension_mismatch_vectors"] == 0
    assert repaired["providers"][0]["dimensions"] == 32
