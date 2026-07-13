from pathlib import Path

from secondbrain.rag.embedding_cache import EmbeddingCache
from secondbrain.rag.batch_embedding_pipeline import BatchEmbeddingPipeline
from secondbrain.rag.retrieval_kpis import evaluate_retrieval
from secondbrain.rag.kpi_store import RetrievalKpiStore
from secondbrain.rag.retrieval_drift_detector import RetrievalDriftDetector


class FakeProvider:
    provider_name = "fake"
    model = "unit"

    def embed(self, texts):
        return [[float(len(text)), 1.0] for text in texts]


def test_embedding_cache_roundtrip(tmp_path):
    cache = EmbeddingCache(tmp_path / "cache.jsonl")
    assert cache.get("hello", provider="fake", model="unit") is None
    cache.put("hello", [1, 2, 3], provider="fake", model="unit")
    assert cache.get("hello", provider="fake", model="unit") == [1.0, 2.0, 3.0]


def test_batch_embedding_pipeline_uses_cache(tmp_path):
    cache = EmbeddingCache(tmp_path / "cache.jsonl")
    pipe = BatchEmbeddingPipeline(FakeProvider(), cache=cache, batch_size=1)
    first = pipe.run(["aa", "bbb"])
    second = pipe.run(["aa", "bbb"])
    assert first.generated == 2
    assert second.cache_hits == 2
    assert second.generated == 0


def test_retrieval_kpis_and_drift_detector():
    metrics = evaluate_retrieval({"a", "c"}, ["b", "a", "c"], k=3)
    assert metrics["recall_at_3"] == 1.0
    assert metrics["mrr"] == 0.5
    drift = RetrievalDriftDetector(min_recall_at_10=0.9)
    assert drift.evaluate({"recall_at_10": 0.5, "mrr": 1.0, "ndcg_at_10": 1.0})["status"] == "FAIL"


def test_kpi_store_summary(tmp_path):
    store = RetrievalKpiStore(tmp_path / "kpis.jsonl")
    store.append("q1", "test", {"mrr": 1.0})
    store.append("q2", "test2", {"mrr": 0.5})
    assert store.summary()["avg_mrr"] == 0.75
