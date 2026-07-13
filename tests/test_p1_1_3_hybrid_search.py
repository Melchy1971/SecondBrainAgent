from secondbrain.rag.providers.deterministic_provider import DeterministicEmbeddingProvider
from secondbrain.rag.retrieval.bm25_search import InMemoryBM25Search, TextChunk
from secondbrain.rag.retrieval.hybrid_search import HybridSearch, HybridSearchConfig
from secondbrain.rag.retrieval.score_fusion import SearchResult, WeightedScoreFusion, normalize_scores
from secondbrain.rag.retrieval.vector_search import InMemoryVectorSearch, VectorChunk


def test_normalize_scores_handles_equal_scores():
    results = [
        SearchResult("doc1", "c1", "a", 5.0),
        SearchResult("doc2", "c2", "b", 5.0),
    ]

    assert normalize_scores(results) == {("doc1", "c1"): 1.0, ("doc2", "c2"): 1.0}


def test_weighted_fusion_merges_duplicates_and_preserves_source_scores():
    fusion = WeightedScoreFusion(vector_weight=0.7, bm25_weight=0.3)
    vector = [SearchResult("doc1", "c1", "alpha", 0.9), SearchResult("doc2", "c2", "beta", 0.1)]
    bm25 = [SearchResult("doc1", "c1", "alpha", 3.0), SearchResult("doc3", "c3", "gamma", 1.0)]

    fused = fusion.fuse(vector, bm25, limit=3)

    assert [r.key for r in fused] == [("doc1", "c1"), ("doc2", "c2"), ("doc3", "c3")]
    assert fused[0].metadata["vector_score"] == 1.0
    assert fused[0].metadata["bm25_score"] == 1.0
    assert fused[0].metadata["fusion"] == "weighted_sum"


def test_bm25_returns_lexically_relevant_chunks_first():
    search = InMemoryBM25Search(
        [
            TextChunk("doc1", "c1", "invoice payment workflow approval"),
            TextChunk("doc2", "c2", "table tennis blade rubber control"),
            TextChunk("doc3", "c3", "payment payment payment reminder"),
        ]
    )

    results = search.search("payment", limit=2)

    assert [r.document_id for r in results] == ["doc3", "doc1"]
    assert all(r.score > 0 for r in results)


def test_vector_search_is_deterministic_and_limited():
    search = InMemoryVectorSearch(
        [
            VectorChunk("doc1", "c1", "same direction", [1.0, 0.0]),
            VectorChunk("doc2", "c2", "opposite", [-1.0, 0.0]),
            VectorChunk("doc3", "c3", "orthogonal", [0.0, 1.0]),
        ]
    )

    results = search.search([1.0, 0.0], limit=2)

    assert [r.document_id for r in results] == ["doc1", "doc3"]


def test_hybrid_search_combines_vector_and_bm25_candidates():
    provider = DeterministicEmbeddingProvider(dimensions=8)
    chunks = [
        TextChunk("doc1", "c1", "privacy mode blocks secret extraction"),
        TextChunk("doc2", "c2", "embedding cache reduces provider calls"),
        TextChunk("doc3", "c3", "calendar reminder automation"),
    ]
    vector_chunks = [
        VectorChunk(c.document_id, c.chunk_id, c.text, provider.embed([c.text])[0])
        for c in chunks
    ]
    hybrid = HybridSearch(
        vector_search=InMemoryVectorSearch(vector_chunks),
        bm25_search=InMemoryBM25Search(chunks),
        embedder=provider,
        config=HybridSearchConfig(vector_weight=0.2, bm25_weight=0.8, candidate_limit=10),
    )

    results = hybrid.search("embedding cache", limit=2)

    assert results
    assert results[0].document_id == "doc2"
    assert results[0].metadata["fusion"] == "weighted_sum"


def test_hybrid_search_rejects_empty_queries_and_non_positive_limits():
    provider = DeterministicEmbeddingProvider(dimensions=8)
    hybrid = HybridSearch(
        vector_search=InMemoryVectorSearch([]),
        bm25_search=InMemoryBM25Search([]),
        embedder=provider,
    )

    assert hybrid.search("", limit=10) == []
    assert hybrid.search("embedding", limit=0) == []
