from secondbrain.storage.pgvector_repository import to_pgvector_literal
from secondbrain.storage.vector_models import VectorRecord
from secondbrain.rag.hybrid_score import HybridScoreCalculator
from secondbrain.rag.vector_search_service import VectorSearchService


class FakeRepo:
    def search(self, query_embedding, limit=10):
        from secondbrain.storage.vector_models import VectorSearchResult
        return [
            VectorSearchResult(
                id="e1",
                owner_type="chunk",
                owner_id="c1",
                distance=0.2,
                score=0.8,
                metadata={"title": "Test"},
            )
        ]


def test_pgvector_literal():
    assert to_pgvector_literal([1, 2.5]) == "[1.0,2.5]"


def test_pgvector_literal_rejects_empty():
    try:
        to_pgvector_literal([])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_vector_record_dimension():
    record = VectorRecord("id", "chunk", "c1", "local", "test", [0.1, 0.2])
    assert record.dimension == 2


def test_hybrid_score():
    score = HybridScoreCalculator().score(
        semantic_score=1.0,
        bm25_score=0.5,
        recency_score=0.5,
        importance_score=0.5,
    )
    assert 0.0 < score <= 1.0


def test_vector_search_service():
    result = VectorSearchService(FakeRepo()).search([0.1], limit=1)
    assert result[0]["hybrid_score"] == 0.8
