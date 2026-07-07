"""Deterministic vector benchmark: batch insert + similarity search latency."""

from __future__ import annotations

from random import Random
from time import perf_counter
from typing import Any

from secondbrain.storage.vector_models import VectorRecord


def make_vectors(count: int, dim: int, *, seed: int = 42, provider: str = "bench",
                 model: str = "bench-model") -> list[VectorRecord]:
    rng = Random(seed)
    out = []
    for i in range(count):
        vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
        out.append(VectorRecord(id=f"v{i}", owner_type="bench", owner_id=str(i),
                                provider=provider, model=model, embedding=vec, metadata={"i": i}))
    return out


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[k]


def run_benchmark(store, *, count: int = 1000, dim: int = 64, queries: int = 20,
                  limit: int = 10, seed: int = 42) -> dict:
    records = make_vectors(count, dim, seed=seed)
    t0 = perf_counter()
    inserted = store.batch_upsert(records)
    insert_seconds = perf_counter() - t0

    rng = Random(seed + 1)
    latencies_ms: list[float] = []
    returned = 0
    for _ in range(queries):
        q = [rng.gauss(0.0, 1.0) for _ in range(dim)]
        s = perf_counter()
        result = store.search(q, limit=limit)
        latencies_ms.append((perf_counter() - s) * 1000.0)
        returned = len(result)

    backend = getattr(store, "dialect", type(store).__name__)
    return {
        "backend": backend,
        "count": count, "dim": dim, "queries": queries, "limit": limit,
        "inserted": inserted,
        "insert_seconds": round(insert_seconds, 6),
        "inserts_per_sec": round(count / insert_seconds, 2) if insert_seconds > 0 else None,
        "search_ms": {
            "p50": round(_percentile(latencies_ms, 50), 4),
            "p95": round(_percentile(latencies_ms, 95), 4),
            "mean": round(sum(latencies_ms) / len(latencies_ms), 4) if latencies_ms else 0.0,
        },
        "returned": returned,
    }
