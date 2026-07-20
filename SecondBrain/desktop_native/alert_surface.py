from __future__ import annotations

from typing import Any, Mapping


def _count(counts: Mapping[str, Any], name: str) -> int:
    try:
        return max(0, int(counts.get(name, 0)))
    except (TypeError, ValueError):
        return 0


def live_alert_labels(*, health: Mapping[str, Any], jobs: Mapping[str, Any]) -> dict[str, str]:
    """Build fixed, payload-free alert labels from existing read-only snapshots."""
    database = str(health.get("database", "Unknown"))
    postgres = {
        "PostgreSQL": "Configured",
        "Local fallback": "Not selected",
        "Blocked": "Blocked",
    }.get(database, "Unknown")

    counts = jobs.get("counts")
    safe_counts = counts if isinstance(counts, Mapping) else {}
    pending = _count(safe_counts, "pending") + _count(safe_counts, "retry")
    blocked = _count(safe_counts, "blocked")
    queue = f"{pending} Pending"
    if blocked:
        queue += f" / {blocked} Blocked"

    return {
        "embedding": str(health.get("embedding", "Unknown")),
        "postgresql": postgres,
        "pgvector": "Not checked",
        "ollama": str(health.get("ollama", "Unknown")),
        "queue": queue,
    }
