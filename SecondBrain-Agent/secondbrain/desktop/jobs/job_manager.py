from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .background_executor import BackgroundExecutor
from .job_history import JobHistory
from .job_registry import JobRegistry
from .job_runner import JobRunner, noop_emit
from .job_state import DesktopJob, JobState

EventEmitter = Callable[[str, dict[str, Any]], None]


@dataclass
class JobManager:
    registry: JobRegistry = field(default_factory=JobRegistry)
    history: JobHistory = field(default_factory=JobHistory)
    emit: EventEmitter = noop_emit
    executor: BackgroundExecutor | None = None
    active_jobs: dict[str, DesktopJob] = field(default_factory=dict)
    queue: list[str] = field(default_factory=list)

    def create_job(self, name: str, metadata: dict[str, Any] | None = None) -> DesktopJob:
        self.registry.get(name)
        job = DesktopJob(name=name, metadata=dict(metadata or {}))
        self.active_jobs[job.job_id] = job
        self.emit("JOB_CREATED", {"job_id": job.job_id, "name": name})
        return job

    def enqueue(self, name: str, metadata: dict[str, Any] | None = None) -> DesktopJob:
        job = self.create_job(name, metadata)
        job.mark_queued()
        self.queue.append(job.job_id)
        self.emit("JOB_QUEUED", {"job_id": job.job_id, "name": name})
        return job

    def run_next(self) -> DesktopJob | None:
        if not self.queue:
            return None
        job_id = self.queue.pop(0)
        return self.run_job(job_id)

    def run_job(self, job_id: str) -> DesktopJob:
        job = self.active_jobs[job_id]
        runner = JobRunner(self.registry, emit=self.emit)
        runner.run(job)
        if job.state.terminal:
            self.history.add(job)
            self.active_jobs.pop(job.job_id, None)
        return job

    def run_async(self, job_id: str):
        if self.executor is None:
            self.executor = BackgroundExecutor()
        return self.executor.submit(self.run_job, job_id)

    def cancel(self, job_id: str) -> DesktopJob:
        job = self.active_jobs[job_id]
        registered = self.registry.get(job.name)
        if not registered.cancellable:
            raise ValueError(f"job is not cancellable: {job.name}")
        if job.state == JobState.RUNNING:
            raise ValueError("running job cannot be cancelled cooperatively yet")
        job.mark_cancelled()
        if job_id in self.queue:
            self.queue.remove(job_id)
        self.history.add(job)
        self.active_jobs.pop(job_id, None)
        self.emit("JOB_CANCELLED", {"job_id": job.job_id, "name": job.name})
        return job

    def progress(self, job_id: str, progress: int) -> DesktopJob:
        job = self.active_jobs[job_id]
        job.mark_progress(progress)
        self.emit("JOB_PROGRESS", {"job_id": job.job_id, "name": job.name, "progress": job.progress})
        return job

    def summary(self) -> dict[str, Any]:
        running = sum(1 for job in self.active_jobs.values() if job.state == JobState.RUNNING)
        failed = len(self.history.failed())
        latest = self.history.latest(1)
        return {
            "active_jobs": len(self.active_jobs),
            "running_jobs": running,
            "queue_length": len(self.queue),
            "failed_jobs": failed,
            "last_finished_at": latest[0].finished_at if latest else None,
        }

    def save_history(self, path: str | Path) -> None:
        self.history.save(path)

    def shutdown(self) -> None:
        if self.executor:
            self.executor.shutdown()
            self.executor = None
