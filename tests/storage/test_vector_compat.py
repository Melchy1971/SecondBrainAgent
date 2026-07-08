"""Guard: existing vector-search APIs remain unchanged (no breaking changes)."""
import inspect
from secondbrain.storage.pgvector_repository import PgVectorRepository, to_pgvector_literal
from secondbrain.storage.vector_index_manager import VectorIndexManager
from secondbrain.storage.vector_models import VectorRecord, VectorSearchResult


def test_pgvector_repository_signature_unchanged():
    params = inspect.signature(PgVectorRepository.search).parameters
    assert "query_embedding" in params
    assert set(["provider", "model", "limit"]).issubset(params)
    assert hasattr(PgVectorRepository, "upsert")


def test_index_manager_hnsw_api_unchanged():
    assert hasattr(VectorIndexManager, "ensure_hnsw_index")
    assert hasattr(VectorIndexManager, "analyze")


def test_pgvector_literal_format():
    assert to_pgvector_literal([1.0, 2.0, 3.0]) == "[1.0,2.0,3.0]"


def test_vector_models_fields_stable():
    assert {f for f in VectorSearchResult.__dataclass_fields__} == {
        "id", "owner_type", "owner_id", "distance", "score", "metadata"}
    assert VectorRecord("i", "o", "oi", "p", "m", [1.0]).dimension == 1
