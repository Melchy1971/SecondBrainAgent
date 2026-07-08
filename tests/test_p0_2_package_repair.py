from dataclasses import dataclass

import pytest

from secondbrain.connectors.incremental_sync import IncrementalSyncEngine
from secondbrain.rag.hybrid_score import HybridScoreCalculator, HybridScoreWeights
from secondbrain.rag.vector_search_service import VectorSearchService


def test_incremental_sync_detects_added_removed_updated_and_unchanged():
    result = IncrementalSyncEngine().compute_changes(
        {"a": "rev1", "b": "rev1", "c": "rev1"},
        {"b": "rev2", "c": "rev1", "d": "rev1"},
    )
    assert result == {
        "added": ["d"],
        "removed": ["a"],
        "updated": ["b"],
        "unchanged": ["c"],
    }


def test_incremental_sync_keeps_legacy_list_contract():
    result = IncrementalSyncEngine().compute_changes(["a", "b"], ["b", "c"])
    assert result["added"] == ["c"]
    assert result["removed"] == ["a"]


def test_hybrid_score_is_bounded_and_weighted():
    score = HybridScoreCalculator().score(
        semantic_score=1.5,
        bm25_score=0.5,
        recency_score=-1.0,
        importance_score=0.5,
    )
    assert score == 0.725


def test_hybrid_score_rejects_invalid_weights():
    with pytest.raises(ValueError):
        HybridScoreCalculator(HybridScoreWeights(semantic=-1.0))


@dataclass
class FakeResult:
    id: str
    owner_type: str
    owner_id: str
    distance: float
    score: float
    metadata: dict


class FakeRepository:
    def search(self, query_embedding, *, limit):
        return [
            FakeResult("low", "doc", "1", 0.2, 0.6, {"bm25_score": 0.1}),
            FakeResult("high", "doc", "2", 0.1, 0.7, {"bm25_score": 1.0, "importance_score": 1.0}),
        ][:limit]


def test_vector_search_service_returns_sorted_hybrid_results():
    results = VectorSearchService(FakeRepository()).search([0.1], limit=2)
    assert [item["id"] for item in results] == ["high", "low"]
    assert results[0]["hybrid_score"] > results[1]["hybrid_score"]
    assert "semantic_score" in results[0]
