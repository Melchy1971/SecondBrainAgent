"""Real pgvector integration - runs only with TEST_DATABASE_URL + sqlalchemy + pgvector."""
import os
import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="set TEST_DATABASE_URL for pgvector integration")


def test_pgvector_roundtrip():
    pytest.importorskip("sqlalchemy")
    from secondbrain.storage.database import Database
    from secondbrain.storage.database_config import DatabaseConfig
    from secondbrain.storage.vector_store import PgVectorStore
    from secondbrain.storage.vector_models import VectorRecord
    store = PgVectorStore(Database(DatabaseConfig(url=TEST_URL)))
    store.reindex(method="hnsw", metric="cosine")
    store.batch_upsert([VectorRecord("t1", "doc", "d1", "p", "m", [1.0, 0.0, 0.0])])
    res = store.search([1.0, 0.0, 0.0], limit=1)
    assert res and res[0].id == "t1"
