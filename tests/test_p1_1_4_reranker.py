import pytest

from secondbrain.rag.reranker import KeywordOverlapScorer, Reranker, RerankerConfig
from secondbrain.rag.retrieval.score_fusion import SearchResult


def test_keyword_overlap_scorer_scores_query_terms():
    scorer = KeywordOverlapScorer()
    result = SearchResult("doc1", "c1", "embedding cache reduces calls", 0.2)

    assert scorer.score("embedding cache", result) == 1.0
    assert scorer.score("calendar cache", result) == 0.5


def test_reranker_prioritizes_semantically_matching_candidate():
    results = [
        SearchResult("doc1", "c1", "calendar reminder automation", 0.9),
        SearchResult("doc2", "c2", "embedding cache provider isolation", 0.2),
    ]

    reranked = Reranker().rerank("embedding cache", results, limit=2)

    assert [r.document_id for r in reranked] == ["doc2", "doc1"]
    assert reranked[0].metadata["rerank_score"] == 1.0
    assert reranked[0].metadata["pre_rerank_score"] == 0.2


def test_reranker_preserves_stable_baseline_when_disabled():
    results = [
        SearchResult("doc2", "c2", "embedding cache", 0.1),
        SearchResult("doc1", "c1", "calendar", 0.9),
    ]

    reranked = Reranker(config=RerankerConfig(enabled=False)).rerank("embedding cache", results, limit=2)

    assert [r.document_id for r in reranked] == ["doc1", "doc2"]


def test_reranker_fails_open_when_external_scorer_breaks():
    class BrokenScorer:
        def score(self, query, result):
            raise RuntimeError("remote scorer unavailable")

    results = [
        SearchResult("doc2", "c2", "embedding cache", 0.1),
        SearchResult("doc1", "c1", "calendar", 0.9),
    ]

    reranked = Reranker(scorer=BrokenScorer(), config=RerankerConfig(fail_open=True)).rerank("embedding", results)

    assert [r.document_id for r in reranked] == ["doc1", "doc2"]


def test_reranker_can_fail_closed_for_gate_validation():
    class BrokenScorer:
        def score(self, query, result):
            raise RuntimeError("remote scorer unavailable")

    with pytest.raises(RuntimeError):
        Reranker(scorer=BrokenScorer(), config=RerankerConfig(fail_open=False)).rerank(
            "embedding", [SearchResult("doc1", "c1", "embedding", 0.1)]
        )


def test_reranker_rejects_invalid_config():
    with pytest.raises(ValueError):
        RerankerConfig(candidate_limit=0)
    with pytest.raises(ValueError):
        RerankerConfig(result_limit=0)
