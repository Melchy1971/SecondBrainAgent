"""Shared lightweight fakes for the v30.62 workflow engine tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class FakeJob:
    id: str
    status: str = "pending"
    error: str | None = None


class FakeJobQueue:
    """Minimal stand-in for JobQueueService that records calls."""

    def __init__(self) -> None:
        self.jobs: dict[str, FakeJob] = {}
        self.status_calls: list[tuple[str, str]] = []
        self._n = 0

    def add_job(self, kind: str, title: str, *, payload: dict | None = None, **_: Any) -> FakeJob:
        self._n += 1
        job = FakeJob(id=f"job_{self._n}")
        self.jobs[job.id] = job
        return job

    def update_status(self, job_id: str, status: str, *, error: str | None = None):
        self.status_calls.append((job_id, status))
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            self.jobs[job_id].error = error
        return self.jobs.get(job_id)


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


class RecordingRunner:
    """tool_runner that records execution order and delegates to per-step fns."""

    def __init__(self, behavior: dict[str, Callable[[], Any]] | None = None, default: Any = "ok") -> None:
        self.behavior = behavior or {}
        self.default = default
        self.calls: list[str] = []

    def __call__(self, step, approved: bool) -> Any:
        self.calls.append(step.id)
        fn = self.behavior.get(step.id)
        if fn is not None:
            return fn()
        return self.default


@dataclass
class MemorySink:
    facts: list[dict] = field(default_factory=list)

    def __call__(self, fact: dict) -> None:
        self.facts.append(fact)
