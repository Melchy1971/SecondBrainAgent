import pytest
from secondbrain.storage.vector_store import SqliteVectorStore
from secondbrain.storage.vector_benchmark import make_vectors
from secondbrain.storage.vector_migrate import migrate_vectors


def test_migrate_copies_all_records():
    src = SqliteVectorStore(":memory:")
    src.batch_upsert(make_vectors(50, 8))
    tgt = SqliteVectorStore(":memory:")
    result = migrate_vectors(src, tgt, batch_size=20)
    assert result["migrated"] == 50 and result["batches"] == 3 and result["target_count"] == 50
    # searchable after migration
    assert tgt.search(src.iter_records().__next__().embedding, limit=1)


def test_migrate_empty_source():
    assert migrate_vectors(SqliteVectorStore(":memory:"), SqliteVectorStore(":memory:"))["migrated"] == 0


def test_batch_size_validation():
    with pytest.raises(ValueError):
        migrate_vectors(SqliteVectorStore(":memory:"), SqliteVectorStore(":memory:"), batch_size=0)
