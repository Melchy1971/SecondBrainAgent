from secondbrain.rag.rrf import RankedItem, reciprocal_rank_fusion
from secondbrain.rag.hybrid_retrieval_v2 import HybridRetrievalV2
from secondbrain.gates.p1_production_gate import P1ProductionGate


class StaticBackend:
    def __init__(self, ids):
        self.ids = ids

    def search(self, query, limit):
        return [RankedItem(id=item_id, payload={"query": query}) for item_id in self.ids[:limit]]


def test_rrf_promotes_items_seen_in_multiple_sources():
    fused = reciprocal_rank_fusion({
        "keyword": [RankedItem("a"), RankedItem("b")],
        "vector": [RankedItem("b"), RankedItem("c")],
    })
    assert fused[0].id == "b"
    assert set(fused[0].sources) == {"keyword", "vector"}


def test_hybrid_retrieval_v2_returns_fused_results():
    retriever = HybridRetrievalV2(
        keyword_backend=StaticBackend(["a", "b"]),
        vector_backend=StaticBackend(["b", "c"]),
    )
    result = retriever.search("test", limit=2)
    assert result.results[0].id == "b"
    assert result.keyword_count == 2
    assert result.vector_count == 2


def test_p1_production_gate_passes_on_thresholds():
    result = P1ProductionGate().evaluate({
        "records": 5,
        "avg_recall_at_10": 0.90,
        "avg_mrr": 0.80,
        "avg_ndcg_at_10": 0.85,
    })
    assert result.status == "PASS"


def test_p1_production_gate_fails_below_thresholds():
    result = P1ProductionGate().evaluate({
        "records": 5,
        "avg_recall_at_10": 0.20,
        "avg_mrr": 0.80,
        "avg_ndcg_at_10": 0.85,
    })
    assert result.status == "FAIL"
