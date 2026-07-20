from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

try:
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional desktop dependency
    psutil = None  # type: ignore[assignment]

_DEFAULT_SOURCE = object()


class SystemMetricsSampler:
    """Add counter-based network rates to the stateless host snapshot."""

    def __init__(self, *, source: Any = _DEFAULT_SOURCE, clock: Callable[[], float] = time.monotonic) -> None:
        self.source = source
        self.clock = clock
        self._network_sample: tuple[float, int, int] | None = None

    def read(self, project_root: str | Path) -> dict[str, Any]:
        provider = psutil if self.source is _DEFAULT_SOURCE else self.source
        metrics = read_system_metrics(project_root, source=provider)
        if not metrics.get("available") or provider is None:
            return metrics
        try:
            counters = provider.net_io_counters()
            now = float(self.clock())
            sent = max(0, int(counters.bytes_sent))
            received = max(0, int(counters.bytes_recv))
        except Exception:  # noqa: BLE001 - optional host counter must not stop the UI timer
            return {**metrics, "network_available": False}

        up_kbps = 0.0
        down_kbps = 0.0
        if self._network_sample is not None:
            previous_time, previous_sent, previous_received = self._network_sample
            elapsed = now - previous_time
            if elapsed > 0:
                up_kbps = max(0.0, (sent - previous_sent) / elapsed / 1024)
                down_kbps = max(0.0, (received - previous_received) / elapsed / 1024)
        self._network_sample = (now, sent, received)
        return {
            **metrics,
            "network_available": True,
            "net_up_kbps": round(up_kbps, 1),
            "net_down_kbps": round(down_kbps, 1),
        }


def read_system_metrics(project_root: str | Path, *, source: Any = _DEFAULT_SOURCE) -> dict[str, Any]:
    """Collect bounded, read-only host metrics and degrade without psutil."""
    provider = psutil if source is _DEFAULT_SOURCE else source
    if provider is None:
        return {"available": False}
    try:
        memory = provider.virtual_memory()
        swap = provider.swap_memory()
        disk = provider.disk_usage(str(Path(project_root).resolve()))
        uptime_seconds = max(0, int(time.time() - float(provider.boot_time())))
        return {
            "available": True,
            "cpu_percent": _percent(provider.cpu_percent(interval=None)),
            "ram_percent": _percent(memory.percent),
            "swap_percent": _percent(swap.percent),
            "disk_percent": _percent(disk.percent),
            "disk_total": max(0, int(disk.total)),
            "disk_used": max(0, int(disk.used)),
            "disk_free": max(0, int(disk.free)),
            "uptime_seconds": uptime_seconds,
        }
    except Exception:  # noqa: BLE001 - optional host provider must not stop the UI timer
        return {"available": False}


def _percent(value: Any) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def format_percent(value: Any) -> str:
    if value is None:
        return "Unavailable"
    return f"{float(value):g}%"


def format_bytes(value: Any) -> str:
    if value is None:
        return "Unavailable"
    gib = max(0, int(value)) / (1024**3)
    return f"{gib:.1f} GiB"


def format_uptime(value: Any) -> str:
    if value is None:
        return "Unavailable"
    days, remainder = divmod(max(0, int(value)), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    return f"{days}d {hours}h {minutes}min"


def format_kbps(value: Any) -> str:
    if value is None:
        return "Unavailable"
    return f"{max(0.0, float(value)):.1f} KB/s"
