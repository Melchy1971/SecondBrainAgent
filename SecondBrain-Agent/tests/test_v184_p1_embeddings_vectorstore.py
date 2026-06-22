from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_embeddings import LocalEmbeddingProvider, cosine_similarity
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_local_embedding_provider_is_deterministic():
    provider = LocalEmbeddingProvider(dimensions=32)
    a = provider.embed("Jarvis lokale Quellen")
    b = provider.embed("Jarvis lokale Quellen")
    c = provider.embed("anderer Inhalt")
    assert a == b
    assert len(a) == 32
    assert cosine_similarity(a, b) > cosine_similarity(a, c)
    assert provider.status()["provider"] == "local-deterministic"


def test_p1_ingest_creates_vectors_and_hybrid_search(tmp_path):
    rt = P1RagRuntime(tmp_path)
    ingest = rt.ingest_text(
        "Jarvis nutzt lokale Quellen. Der VectorStore speichert Embeddings für Hybrid Retrieval.",
        source="unit://v184",
        title="VectorStore",
    )
    assert ingest["ok"] is True
    embedding_status = rt.embedding_status()
    assert embedding_status["ok"] is True
    assert embedding_status["indexed_vectors"][0]["chunks"] == ingest["chunks"]
    vector = rt.vector_search("Embeddings Hybrid", 3)
    assert vector["ok"] is True
    assert vector["hit_count"] >= 1
    hybrid = rt.hybrid_search("lokale Quellen VectorStore", 3)
    assert hybrid["schema"] == "secondbrain.p1_hybrid.search.v1"
    assert hybrid["hit_count"] >= 1
    assert "hybrid_score" in hybrid["hits"][0]


def test_p1_reindex_benchmark_and_gate_v4(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Benchmark")
    reindex = rt.reindex_vectors(write_report=True)
    assert reindex["ok"] is True
    assert (tmp_path / "runtime" / "reports" / "p1_vector_reindex_latest.json").exists()
    benchmark = rt.retrieval_benchmark(write_report=True)
    assert benchmark["schema"] == "secondbrain.p1_retrieval.benchmark.v1"
    assert benchmark["hit_rate"] > 0
    gate = rt.gate(write_report=True)
    assert gate["schema"] == "secondbrain.p1_gate.v4"
    assert gate["ok"] is True
    assert json.loads((tmp_path / "runtime" / "reports" / "p1_gate_latest.json").read_text(encoding="utf-8"))["schema"] == "secondbrain.p1_gate.v4"


def test_p1_v184_launcher_commands_and_registry(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis Embeddings Hybrid Retrieval", "--source", "unit", "--title", "CLI"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-embedding-status"]) == 0
    assert "secondbrain.p1_embeddings.status.v1" in capsys.readouterr().out
    assert main(["--project-root", str(tmp_path), "p1-rag-hybrid-search", "Hybrid Retrieval"]) == 0
    assert "secondbrain.p1_hybrid.search.v1" in capsys.readouterr().out
    assert main(["--project-root", str(tmp_path), "p1-rag-reindex", "--write-report"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-retrieval-benchmark", "--write-report"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-gate", "--write-report"]) == 0
    assert "secondbrain.p1_gate.v4" in capsys.readouterr().out
    index = ModuleRegistry().command_index()
    assert index["p1-embedding-status"] == "core"
    assert index["p1-rag-hybrid-search"] == "core"
    assert index["p1-retrieval-benchmark"] == "core"
