import pytest
from secondbrain.storage.vector_store import SqliteVectorStore, distance
from secondbrain.storage.vector_models import VectorRecord, VectorSearchResult


def _store():
    s = SqliteVectorStore(":memory:")
    s.batch_upsert([
        VectorRecord("a", "doc", "d1", "p1", "m1", [1.0, 0.0, 0.0]),
        VectorRecord("b", "doc", "d2", "p1", "m1", [0.0, 1.0, 0.0]),
        VectorRecord("c", "doc", "d3", "p2", "m2", [0.9, 0.1, 0.0]),
    ])
    return s


def test_cosine_search_orders_and_scores():
    s = _store()
    res = s.search([1.0, 0.0, 0.0], limit=3)
    assert [r.id for r in res][:2] == ["a", "c"]
    assert isinstance(res[0], VectorSearchResult)
    assert res[0].score == pytest.approx(1.0)               # identical to existing cosine semantics
    assert res[0].score == pytest.approx(1.0 - res[0].distance)


def test_provider_and_model_filter():
    s = _store()
    res = s.search([1.0, 0.0, 0.0], provider="p2", limit=5)
    assert [r.id for r in res] == ["c"]


def test_metrics_l2_and_ip():
    s = _store()
    assert s.search([1.0, 0.0, 0.0], metric="l2", limit=1)[0].id == "a"
    assert s.search([1.0, 0.0, 0.0], metric="ip", limit=1)[0].id == "a"


def test_upsert_conflict_updates():
    s = SqliteVectorStore(":memory:")
    s.upsert(VectorRecord("x", "doc", "d", "p", "m", [1.0, 0.0]))
    s.upsert(VectorRecord("x", "doc", "d", "p", "m", [0.0, 1.0]))
    assert s.count() == 1
    assert s.search([0.0, 1.0], limit=1)[0].score == pytest.approx(1.0)


def test_limit_validation_and_explain_and_reindex():
    s = _store()
    with pytest.raises(ValueError):
        s.search([1.0, 0.0, 0.0], limit=0)
    assert s.explain([1.0, 0.0, 0.0])["backend"] == "sqlite"
    assert s.reindex(method="hnsw")["status"] == "noop"


def test_distance_functions():
    assert distance("cosine", [1, 0], [1, 0]) == pytest.approx(0.0)
    assert distance("l2", [0, 0], [3, 4]) == pytest.approx(5.0)
