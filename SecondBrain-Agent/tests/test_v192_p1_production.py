from __future__ import annotations

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_retrieval import evaluate_ranked_hits, reciprocal_rank_fusion
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_rrf_fusion_is_deterministic_and_preserves_sources():
    keyword = [
        {"chunk_id": "a", "title": "A", "score": 10, "retrieval_source": "keyword"},
        {"chunk_id": "b", "title": "B", "score": 4, "retrieval_source": "keyword"},
    ]
    vector = [
        {"chunk_id": "b", "title": "B", "score": 0.9, "retrieval_source": "vector"},
        {"chunk_id": "c", "title": "C", "score": 0.7, "retrieval_source": "vector"},
    ]
    fused = reciprocal_rank_fusion([keyword, vector], weights=[1.0, 1.0])
    assert [hit["chunk_id"] for hit in fused][:2] == ["b", "a"]
    assert fused[0]["rank_sources"] == ["keyword", "vector"]


def test_retrieval_metrics_compute_recall_mrr_ndcg():
    hits = [{"text": "Jarvis nutzt lokale RAG Quellen"}, {"text": "andere Notiz"}]
    metrics = evaluate_ranked_hits(hits, ["jarvis", "rag", "quellen"], k=2)
    assert metrics["recall_at_k"] == 1.0
    assert metrics["mrr"] == 1.0
    assert metrics["ndcg"] == 1.0


def test_p1_production_gate_passes_with_seed_content(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text(
        "Jarvis RAG Quellen liefern lokale Quellen. Memory Evidenz wird mit Zitaten geprüft.",
        source="unit://v192",
        title="P1 Production Seed",
    )
    hybrid = rt.hybrid_search("Jarvis RAG Quellen", 3)
    assert hybrid["models"]["fusion"] == "rrf_v1"
    assert hybrid["hit_count"] >= 1
    metrics = rt.retrieval_metrics(write_report=True)
    assert metrics["schema"] == "secondbrain.p1_retrieval.metrics.v1"
    assert metrics["avg_recall_at_k"] >= 0.75
    production = rt.production_gate(write_report=True)
    assert production["schema"] == "secondbrain.p1_production.v1"
    assert production["ok"] is False
    assert (tmp_path / "runtime" / "reports" / "p1_production_latest.json").exists()


def test_p1_production_launcher_and_registry(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen Memory Evidenz lokale Quellen", "--source", "unit", "--title", "Prod"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-retrieval-metrics", "--write-report"]) == 0
    assert "secondbrain.p1_retrieval.metrics.v1" in capsys.readouterr().out
    assert main(["--project-root", str(tmp_path), "p1-production", "--write-report"]) == 1
    assert "secondbrain.p1_production.v1" in capsys.readouterr().out
    index = ModuleRegistry().command_index()
    assert index["p1-retrieval-metrics"] == "core"
    assert index["p1-production"] == "core"
