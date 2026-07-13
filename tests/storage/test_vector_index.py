import pytest
from secondbrain.storage import vector_index as vi


def test_hnsw_ddl():
    sql = vi.hnsw_index_sql(metric="cosine", m=32, ef_construction=100)
    assert "USING hnsw" in sql and "vector_cosine_ops" in sql
    assert "m = 32" in sql and "ef_construction = 100" in sql
    assert "IF NOT EXISTS" in sql


def test_ivfflat_ddl():
    sql = vi.ivfflat_index_sql(metric="l2", lists=200)
    assert "USING ivfflat" in sql and "vector_l2_ops" in sql and "lists = 200" in sql


def test_operator_and_opclass_maps():
    assert vi.OPERATOR["cosine"] == "<=>" and vi.OPERATOR["l2"] == "<->" and vi.OPERATOR["ip"] == "<#>"
    assert vi.index_name("hnsw", "cosine") == "idx_embeddings_hnsw_cosine"


def test_unsupported_metric_raises():
    with pytest.raises(ValueError):
        vi.hnsw_index_sql(metric="hamming")
