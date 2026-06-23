"""Metrics snapshot for Search RC1."""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class SearchMetricsSnapshot:
    search_latency_ms: float = 0.0
    preview_latency_ms: float = 0.0
    saved_search_load_ms: float = 0.0
    result_count: int = 0
    history_size: int = 0
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "search_latency_ms": round(self.search_latency_ms, 3),
            "preview_latency_ms": round(self.preview_latency_ms, 3),
            "saved_search_load_ms": round(self.saved_search_load_ms, 3),
            "result_count": self.result_count,
            "history_size": self.history_size,
            "metadata": dict(self.metadata),
        }


class SearchMetricsCollector:
    def __init__(self) -> None:
        self.snapshot = SearchMetricsSnapshot()

    def measure(self, field_name: str, fn: Callable[[], T]) -> T:
        start = perf_counter()
        try:
            return fn()
        finally:
            elapsed = (perf_counter() - start) * 1000
            if not hasattr(self.snapshot, field_name):
                raise AttributeError(f"Unknown search metric: {field_name}")
            setattr(self.snapshot, field_name, elapsed)

    def set_counts(self, *, result_count: int = 0, history_size: int = 0) -> None:
        self.snapshot.result_count = max(0, int(result_count))
        self.snapshot.history_size = max(0, int(history_size))
