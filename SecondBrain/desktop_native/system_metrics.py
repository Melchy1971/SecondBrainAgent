from __future__ import annotations

import time
from pathlib import Path
from typing import Any

try:
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional desktop dependency
    psutil = None  # type: ignore[assignment]

_DEFAULT_SOURCE = object()


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
