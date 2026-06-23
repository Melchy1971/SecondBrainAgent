"""Runtime metrics for RAG retrieval pipelines.

P1.1.6 provides dependency-free metrics primitives for retrieval execution.
The collector records latency, counters and context shape without binding the
core RAG package to a specific observability backend.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterator, Mapping


@dataclass(frozen=True)
class RetrievalMetricsSnapshot:
    """Immutable export format for one retrieval execution or aggregate window."""

    retrieval_latency_ms: float = 0.0
    embedding_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    chunks_returned: int = 0
    tokens_context: int = 0
    counters: Mapping[str, int] = field(default_factory=dict)

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return 0.0 if total == 0 else self.cache_hits / total

    def to_dict(self) -> dict[str, float | int | dict[str, int]]:
        return {
            "retrieval_latency_ms": round(self.retrieval_latency_ms, 3),
            "embedding_latency_ms": round(self.embedding_latency_ms, 3),
            "rerank_latency_ms": round(self.rerank_latency_ms, 3),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hit_rate, 6),
            "chunks_returned": self.chunks_returned,
            "tokens_context": self.tokens_context,
            "counters": dict(self.counters),
        }


class RetrievalMetricsCollector:
    """Collect latency and volume metrics for one RAG request.

    The collector is intentionally local and deterministic. It can be used in
    tests, CLIs and services, then exported to logs, JSON, Prometheus adapters
    or application-level KPI stores.
    """

    _KNOWN_LATENCIES = {
        "retrieval": "retrieval_latency_ms",
        "embedding": "embedding_latency_ms",
        "rerank": "rerank_latency_ms",
    }

    def __init__(self) -> None:
        self._latencies_ms: dict[str, float] = {
            "retrieval_latency_ms": 0.0,
            "embedding_latency_ms": 0.0,
            "rerank_latency_ms": 0.0,
        }
        self._cache_hits = 0
        self._cache_misses = 0
        self._chunks_returned = 0
        self._tokens_context = 0
        self._counters: dict[str, int] = {}

    @contextmanager
    def timer(self, name: str) -> Iterator[None]:
        """Measure a named stage and add elapsed milliseconds to the snapshot.

        Supported canonical names are ``retrieval``, ``embedding`` and
        ``rerank``. Unknown names are tracked as ``<name>_latency_ms`` counters
        in the generic counter map using integer milliseconds.
    """

        if not name or not isinstance(name, str):
            raise ValueError("timer name must be a non-empty string")
        start = perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (perf_counter() - start) * 1000.0
            field_name = self._KNOWN_LATENCIES.get(name)
            if field_name:
                self._latencies_ms[field_name] += elapsed_ms
            else:
                self.increment(f"{name}_latency_ms", int(round(elapsed_ms)))

    def record_latency(self, name: str, milliseconds: float) -> None:
        if milliseconds < 0:
            raise ValueError("milliseconds must be >= 0")
        field_name = self._KNOWN_LATENCIES.get(name)
        if field_name is None:
            self.increment(f"{name}_latency_ms", int(round(milliseconds)))
            return
        self._latencies_ms[field_name] += float(milliseconds)

    def record_cache(self, *, hit: bool, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        if hit:
            self._cache_hits += count
        else:
            self._cache_misses += count

    def record_context(self, *, chunks_returned: int, tokens_context: int) -> None:
        if chunks_returned < 0 or tokens_context < 0:
            raise ValueError("context metrics must be >= 0")
        self._chunks_returned = chunks_returned
        self._tokens_context = tokens_context

    def increment(self, name: str, amount: int = 1) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("counter name must be a non-empty string")
        if amount < 0:
            raise ValueError("amount must be >= 0")
        self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> RetrievalMetricsSnapshot:
        return RetrievalMetricsSnapshot(
            retrieval_latency_ms=self._latencies_ms["retrieval_latency_ms"],
            embedding_latency_ms=self._latencies_ms["embedding_latency_ms"],
            rerank_latency_ms=self._latencies_ms["rerank_latency_ms"],
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            chunks_returned=self._chunks_returned,
            tokens_context=self._tokens_context,
            counters=dict(self._counters),
        )

    def reset(self) -> None:
        self.__init__()


def summarize_retrieval(
    *,
    retrieval_latency_ms: float = 0.0,
    embedding_latency_ms: float = 0.0,
    rerank_latency_ms: float = 0.0,
    cache_hits: int = 0,
    cache_misses: int = 0,
    chunks_returned: int = 0,
    tokens_context: int = 0,
) -> RetrievalMetricsSnapshot:
    """Create a validated snapshot without a mutable collector."""

    collector = RetrievalMetricsCollector()
    collector.record_latency("retrieval", retrieval_latency_ms)
    collector.record_latency("embedding", embedding_latency_ms)
    collector.record_latency("rerank", rerank_latency_ms)
    collector.record_cache(hit=True, count=cache_hits)
    collector.record_cache(hit=False, count=cache_misses)
    collector.record_context(chunks_returned=chunks_returned, tokens_context=tokens_context)
    return collector.snapshot()
