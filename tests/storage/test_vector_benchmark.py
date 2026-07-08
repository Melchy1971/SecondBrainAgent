from secondbrain.storage.vector_store import SqliteVectorStore
from secondbrain.storage.vector_benchmark import make_vectors, run_benchmark


def test_make_vectors_is_deterministic():
    a = make_vectors(5, 4, seed=7)
    b = make_vectors(5, 4, seed=7)
    assert [r.embedding for r in a] == [r.embedding for r in b]
    assert a[0].embedding != a[1].embedding


def test_benchmark_structure():
    report = run_benchmark(SqliteVectorStore(":memory:"), count=200, dim=16, queries=10, limit=5)
    assert report["inserted"] == 200 and report["returned"] == 5
    assert set(report["search_ms"]) == {"p50", "p95", "mean"}
    assert report["inserts_per_sec"] is None or report["inserts_per_sec"] > 0
