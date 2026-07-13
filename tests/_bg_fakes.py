"""Shared fakes for v30.63 background-agent tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeJob:
    id: str
    kind: str = "agent"
    status: str = "pending"
    error: str | None = None


class FakeJobs:
    """Stand-in for JobQueueService: workflow mirroring + snapshot()."""

    def __init__(self, snapshot_health: str = "ok") -> None:
        self.jobs: dict[str, FakeJob] = {}
        self.status_calls: list[tuple[str, str]] = []
        self.snapshot_health = snapshot_health
        self._n = 0

    def add_job(self, kind: str, title: str, *, payload: dict | None = None, **_: Any) -> FakeJob:
        self._n += 1
        job = FakeJob(id=f"job_{self._n}", kind=kind)
        self.jobs[job.id] = job
        return job

    def update_status(self, job_id: str, status: str, *, error: str | None = None):
        self.status_calls.append((job_id, status))
        if job_id in self.jobs:
            self.jobs[job_id].status = status
        return self.jobs.get(job_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "total": len(self.jobs),
            "health": self.snapshot_health,
            "jobs": [{"kind": j.kind, "status": j.status} for j in self.jobs.values()],
        }


class FakeNotifications:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def notify(self, title: str, message: str, *, level: str = "info", category: str = "system",
               source: str = "native", action_required: bool = False, actions=None, metadata=None):
        self.sent.append({
            "title": title, "message": message, "level": level, "category": category,
            "action_required": action_required, "metadata": metadata or {},
        })
        return {"ok": True}


@dataclass
class MemorySink:
    facts: list[dict] = field(default_factory=list)

    def __call__(self, fact: dict) -> None:
        self.facts.append(fact)


def make_supervisor(tmp_path, **overrides):
    from secondbrain.agent.background_agents import AgentSupervisor

    jobs = overrides.pop("jobs", None) or FakeJobs()
    notifications = overrides.pop("notifications", None) or FakeNotifications()
    sup = AgentSupervisor(tmp_path, jobs=jobs, notifications=notifications, **overrides)
    return sup, jobs, notifications
