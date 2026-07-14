"""Performance measurement harness.

Measures wall time, CPU, RAM delta, disk IO and (optionally) DB time for a
callable, using psutil when available and degrading gracefully otherwise. The
harness runs a callable N times and reports per-iteration cost so short
components produce stable numbers.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

try:  # psutil is optional; without it only wall time is reported.
    import psutil

    _PROC = psutil.Process(os.getpid())
    _HAS_PSUTIL = True
except Exception:  # noqa: BLE001
    psutil = None  # type: ignore
    _PROC = None
    _HAS_PSUTIL = False

__all__ = ["Measurement", "BenchmarkResult", "measure", "has_psutil"]


def has_psutil() -> bool:
    return _HAS_PSUTIL


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _io_counters() -> tuple[int, int]:
    if not _HAS_PSUTIL:
        return (0, 0)
    try:
        c = _PROC.io_counters()  # type: ignore[union-attr]
        return (int(c.read_bytes), int(c.write_bytes))
    except Exception:  # noqa: BLE001 - not available on every platform
        return (0, 0)


def _rss_mb() -> float:
    if not _HAS_PSUTIL:
        return 0.0
    try:
        return _PROC.memory_info().rss / 1e6  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        return 0.0


def _cpu_seconds() -> float:
    if not _HAS_PSUTIL:
        return 0.0
    try:
        t = _PROC.cpu_times()  # type: ignore[union-attr]
        return float(t.user + t.system)
    except Exception:  # noqa: BLE001
        return 0.0


@dataclass
class Measurement:
    seconds: float
    per_iter_ms: float
    cpu_percent: float
    ram_delta_mb: float
    io_read_kb: float
    io_write_kb: float
    db_ms: float
    iterations: int


@dataclass
class BenchmarkResult:
    component: str
    case: str
    status: str  # ok | requires_service | error
    metrics: dict[str, float]
    detail: str = ""
    timestamp: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "case": self.case,
            "status": self.status,
            "metrics": dict(self.metrics),
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


def measure(fn: Callable[[], Any], *, iterations: int = 1) -> Measurement:
    """Run ``fn`` ``iterations`` times and return aggregate resource metrics.

    If ``fn`` returns a mapping containing ``db_ms``, that value is summed as the
    database time contribution (lets DB-bound cases report query time).
    """

    iterations = max(1, int(iterations))
    io0 = _io_counters()
    cpu0 = _cpu_seconds()
    rss0 = _rss_mb()
    db_ms_total = 0.0
    start = time.perf_counter()
    for _ in range(iterations):
        result = fn()
        if isinstance(result, dict) and "db_ms" in result:
            try:
                db_ms_total += float(result["db_ms"] or 0.0)
            except (TypeError, ValueError):
                pass
    wall = time.perf_counter() - start
    io1 = _io_counters()
    cpu1 = _cpu_seconds()
    rss1 = _rss_mb()

    cpu_delta = max(0.0, cpu1 - cpu0)
    cpu_percent = round(cpu_delta / wall * 100.0, 1) if wall > 0 else 0.0
    return Measurement(
        seconds=round(wall, 6),
        per_iter_ms=round(wall / iterations * 1000.0, 4),
        cpu_percent=cpu_percent,
        ram_delta_mb=round(max(0.0, rss1 - rss0), 3),
        io_read_kb=round(max(0, io1[0] - io0[0]) / 1024.0, 2),
        io_write_kb=round(max(0, io1[1] - io0[1]) / 1024.0, 2),
        db_ms=round(db_ms_total, 3),
        iterations=iterations,
    )
