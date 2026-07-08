from secondbrain.desktop.search import SearchQuery, SearchService
from secondbrain.desktop.search.hybrid_search_ui import (
    HybridCandidate,
    HybridSearchBackendAdapter,
    HybridSearchSettings,
)


class FakeHybridEngine:
    def __init__(self, candidates):
        self.candidates = candidates
        self.calls = []

    def search(self, query, *, limit: int):
        self.calls.append((query, limit))
        return self.candidates[:limit]


def test_hybrid_settings_normalize_weights_and_limit_multiplier():
    settings = HybridSearchSettings(vector_weight=4, bm25_weight=1, limit_multiplier=99).normalized()
    assert settings.vector_weight == 0.8
    assert settings.bm25_weight == 0.2
    assert settings.limit_multiplier == 10


def test_hybrid_settings_fallback_when_weights_are_zero():
    settings = HybridSearchSettings(vector_weight=0, bm25_weight=0).normalized()
    assert settings.vector_weight == 0.65
    assert settings.bm25_weight == 0.35


def test_adapter_ranks_by_weighted_hybrid_score():
    engine = FakeHybridEngine([
        HybridCandidate("a", "Vector Hit", "semantic", vector_score=0.9, bm25_score=0.1),
        HybridCandidate("b", "Keyword Hit", "exact", vector_score=0.2, bm25_score=1.0),
    ])
    adapter = HybridSearchBackendAdapter(engine, HybridSearchSettings(vector_weight=0.25, bm25_weight=0.75))
    results = adapter.search(SearchQuery("test"))
    assert [r.document_id for r in results] == ["b", "a"]
    assert results[0].metadata["score_source"] == "hybrid"
    assert results[0].metadata["bm25_score"] == 1.0


def test_adapter_coerces_dict_candidates():
    engine = FakeHybridEngine([
        {"id": "1", "title": "Doc", "text": "body", "vector_score": 0.4, "bm25_score": 0.6, "tags": ["rag"]}
    ])
    result = HybridSearchBackendAdapter(engine).search(SearchQuery("doc"))[0]
    assert result.document_id == "1"
    assert result.title == "Doc"
    assert result.tags == ["rag"]
    assert result.score > 0


def test_adapter_honors_query_limit_offset_and_candidate_multiplier():
    engine = FakeHybridEngine([
        HybridCandidate(str(i), f"Doc {i}", "x", vector_score=float(i), bm25_score=0.0)
        for i in range(10)
    ])
    adapter = HybridSearchBackendAdapter(engine, HybridSearchSettings(limit_multiplier=2))
    results = adapter.search(SearchQuery("x", limit=2, offset=1))
    assert len(results) == 2
    assert engine.calls[0][1] == 5


def test_hybrid_adapter_works_inside_search_service():
    engine = FakeHybridEngine([
        HybridCandidate("1", "RAG Plan", "hybrid retrieval", vector_score=0.8, bm25_score=0.7, workspace_id="w1"),
    ])
    service = SearchService(HybridSearchBackendAdapter(engine))
    results, facets = service.search(SearchQuery("rag", workspace_id="w1"))
    assert results[0].document_id == "1"
    assert facets.workspaces[0].value == "w1"
    assert service.history.entries[0]["result_count"] == 1
