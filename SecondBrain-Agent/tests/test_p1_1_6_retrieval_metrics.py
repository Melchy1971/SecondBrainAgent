from __future__ import annotations

import time

import pytest

from secondbrain.rag.metrics import RetrievalMetricsCollector, summarize_retrieval


def test_metrics_snapshot_exports_expected_fields() -> None:
    snapshot = summarize_retrieval(
        retrieval_latency_ms=12.25,
        embedding_latency_ms=5.5,
        rerank_latency_ms=2.0,
        cache_hits=3,
        cache_misses=1,
        chunks_returned=8,
        tokens_context=420,
    )

    data = snapshot.to_dict()

    assert data["retrieval_latency_ms"] == 12.25
    assert data["embedding_latency_ms"] == 5.5
    assert data["rerank_latency_ms"] == 2.0
    assert data["cache_hits"] == 3
    assert data["cache_misses"] == 1
    assert data["cache_hit_rate"] == 0.75
    assert data["chunks_returned"] == 8
    assert data["tokens_context"] == 420


def test_collector_accumulates_cache_and_context_metrics() -> None:
    collector = RetrievalMetricsCollector()

    collector.record_cache(hit=True, count=2)
    collector.record_cache(hit=False, count=3)
    collector.record_context(chunks_returned=5, tokens_context=900)
    collector.increment("hybrid_results", 7)

    snapshot = collector.snapshot()

    assert snapshot.cache_hits == 2
    assert snapshot.cache_misses == 3
    assert snapshot.cache_hit_rate == pytest.approx(0.4)
    assert snapshot.chunks_returned == 5
    assert snapshot.tokens_context == 900
    assert snapshot.counters["hybrid_results"] == 7


def test_timer_records_positive_latency() -> None:
    collector = RetrievalMetricsCollector()

    with collector.timer("retrieval"):
        time.sleep(0.001)

    assert collector.snapshot().retrieval_latency_ms > 0


def test_unknown_timer_is_exported_as_counter() -> None:
    collector = RetrievalMetricsCollector()

    collector.record_latency("compression", 3.6)

    assert collector.snapshot().counters["compression_latency_ms"] == 4


def test_metrics_reject_negative_values() -> None:
    collector = RetrievalMetricsCollector()

    with pytest.raises(ValueError):
        collector.record_latency("retrieval", -1)
    with pytest.raises(ValueError):
        collector.record_cache(hit=True, count=-1)
    with pytest.raises(ValueError):
        collector.record_context(chunks_returned=-1, tokens_context=0)
    with pytest.raises(ValueError):
        collector.increment("x", -1)


def test_reset_clears_collector_state() -> None:
    collector = RetrievalMetricsCollector()
    collector.record_cache(hit=True, count=1)
    collector.record_context(chunks_returned=1, tokens_context=10)

    collector.reset()

    snapshot = collector.snapshot()
    assert snapshot.cache_hits == 0
    assert snapshot.chunks_returned == 0
    assert snapshot.tokens_context == 0
