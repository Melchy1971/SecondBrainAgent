from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Mapping

MONTHS_DE = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def calendar_month(now: datetime) -> str:
    return f"{MONTHS_DE[now.month - 1]} {now.year}"


def runtime_log_level(env: Mapping[str, str] | None = None) -> str:
    values = env if env is not None else os.environ
    raw = str(values.get("SECONDBRAIN_LOG_LEVEL") or values.get("LOG_LEVEL") or "").strip().upper()
    if not raw:
        return "INFO (default)"
    return raw if raw in LOG_LEVELS else "Unknown"


def release_blocker_count(payload: Mapping[str, Any]) -> int:
    native = payload.get("blockers")
    bootstrap = payload.get("bootstrap")
    bootstrap_blockers = bootstrap.get("blockers") if isinstance(bootstrap, Mapping) else None
    return (len(native) if isinstance(native, list) else 0) + (
        len(bootstrap_blockers) if isinstance(bootstrap_blockers, list) else 0
    )


def topbar_status_labels(health: Mapping[str, Any], *, blocker_count: Any) -> dict[str, str]:
    try:
        blockers = max(0, int(blocker_count))
    except (TypeError, ValueError):
        blockers = 0
    database = str(health.get("database", "Unknown"))
    postgres = {
        "PostgreSQL": "Configured",
        "Local fallback": "Not selected",
        "Blocked": "Blocked",
    }.get(database, "Unknown")
    return {
        "release_gate": "READY" if blockers == 0 else f"BLOCKING {blockers}",
        "embedding": str(health.get("embedding", "Unknown")),
        "postgresql": postgres,
    }
