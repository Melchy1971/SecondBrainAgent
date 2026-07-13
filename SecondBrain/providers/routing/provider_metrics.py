"""v30.0 provider metrics."""
from __future__ import annotations

from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class ProviderMetric:
    provider: str
    operation: str
    latency_ms: float
    success: bool
    timestamp: float


class ProviderMetrics:
    def __init__(self) -> None:
        self._items: list[ProviderMetric] = []

    def record(self, provider: str, operation: str, latency_ms: float, success: bool) -> None:
        self._items.append(ProviderMetric(provider, operation, latency_ms, success, time()))

    def list(self) -> list[ProviderMetric]:
        return list(self._items)

    def summary(self) -> dict[str, float | int]:
        total = len(self._items)
        failures = sum(1 for item in self._items if not item.success)
        avg_latency = 0.0 if total == 0 else sum(item.latency_ms for item in self._items) / total
        return {"calls": total, "failures": failures, "avg_latency_ms": round(avg_latency, 2)}
