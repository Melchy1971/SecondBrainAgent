"""v30.71 Scheduler - built-in maintenance jobs.

Recurring maintenance defined as ``RecurringJob``s plus lightweight handlers that
reuse existing subsystems (Job Queue snapshot, memory sink). Each firing is
mirrored into the native Job Queue by the scheduler.
"""

from __future__ import annotations

from typing import Any, Callable

from .models import RecurringJob

# name, cron, queue-kind
MAINTENANCE_DEFS = [
    ("health_check", "*/15 * * * *", "system"),
    ("auto_index", "0 * * * *", "reindex"),
    ("knowledge_refresh", "0 3 * * *", "reindex"),
    ("memory_consolidation", "0 4 * * *", "memory"),
]


def maintenance_jobs() -> list[RecurringJob]:
    jobs = []
    for name, cron, kind in MAINTENANCE_DEFS:
        jobs.append(RecurringJob.create(name, cron, kind=kind, job_id=f"maint_{name}"))
    # knowledge_refresh depends on a fresh index
    for j in jobs:
        if j.name == "knowledge_refresh":
            j.dependencies = ["maint_auto_index"]
    return jobs


# -- handlers ---------------------------------------------------------------
def health_check(scheduler, job) -> dict[str, Any]:
    snap = scheduler.jobs.snapshot()
    return {"checked": "health", "queue_health": snap.get("health", "unknown"),
            "queue_total": snap.get("total", 0)}


def auto_index(scheduler, job) -> dict[str, Any]:
    return {"checked": "auto_index", "reindex_requested": True}


def knowledge_refresh(scheduler, job) -> dict[str, Any]:
    return {"checked": "knowledge_refresh", "refreshed": True}


def memory_consolidation(scheduler, job) -> dict[str, Any]:
    delivered = False
    if scheduler.memory_sink is not None:
        scheduler.memory_sink({"kind": "memory_consolidation", "job_id": job.id})
        delivered = True
    return {"checked": "memory_consolidation", "consolidated": True, "memory_delivered": delivered}


MAINTENANCE_HANDLERS: dict[str, Callable[[Any, Any], dict]] = {
    "health_check": health_check,
    "auto_index": auto_index,
    "knowledge_refresh": knowledge_refresh,
    "memory_consolidation": memory_consolidation,
}
