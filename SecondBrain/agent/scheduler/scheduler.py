"""v30.71 Scheduler - JobScheduler.

Recurring / cron jobs with a dependency-aware run cycle. Every firing is enqueued
into the existing native Job Queue (``JobQueueService``) - no second queue. A
lightweight handler performs the actual maintenance/health/refresh work.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .cron import parse_schedule
from .maintenance import MAINTENANCE_HANDLERS, maintenance_jobs
from .models import JobRun, RecurringJob, new_id, parse_ts, utc_now
from .store import SchedulerStore

RUN_SUCCESS = "success"
RUN_FAILED = "failed"
RUN_SKIPPED = "skipped"


class JobScheduler:
    def __init__(
        self,
        project_root: str | Path,
        *,
        jobs_service: Any | None = None,
        handlers: dict[str, Callable[[Any, RecurringJob], dict]] | None = None,
        memory_sink: Callable[[dict], None] | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.store = SchedulerStore(self.project_root)
        self.jobs = jobs_service
        if self.jobs is None:
            from secondbrain.native.job_queue_center.service import JobQueueService
            self.jobs = JobQueueService(root=self.project_root)
        self.handlers = dict(MAINTENANCE_HANDLERS)
        if handlers:
            self.handlers.update(handlers)
        self.memory_sink = memory_sink

    # -- registration ------------------------------------------------------
    def register(self, job: RecurringJob) -> RecurringJob:
        return self.store.upsert(job)

    def add(self, name: str, schedule: dict | str, *, kind: str = "system",
            payload: dict | None = None, dependencies: list[str] | None = None,
            job_id: str | None = None) -> RecurringJob:
        return self.register(RecurringJob.create(name, schedule, kind=kind, payload=payload,
                                                 dependencies=dependencies, job_id=job_id))

    def register_maintenance(self) -> list[RecurringJob]:
        registered = []
        for job in maintenance_jobs():
            registered.append(self.register(job))
        return registered

    def list(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self.store.load_jobs().values()]

    def runs(self, job_id: str | None = None, *, limit: int = 50) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.store.runs(job_id, limit=limit)]

    # -- due detection -----------------------------------------------------
    def due_jobs(self, *, now: datetime | None = None) -> list[RecurringJob]:
        current = now or datetime.now(timezone.utc)
        out = []
        for job in self.store.load_jobs().values():
            if not job.enabled:
                continue
            schedule = parse_schedule(job.schedule)
            if schedule.due(parse_ts(job.last_run_at), current):
                out.append(job)
        return out

    # -- run cycle ---------------------------------------------------------
    def run_due(self, *, now: datetime | None = None) -> list[JobRun]:
        current = now or datetime.now(timezone.utc)
        all_jobs = self.store.load_jobs()
        due = {j.id: j for j in self.due_jobs(now=current)}
        ordered = self._topological(list(due.values()), all_jobs)

        cycle_status: dict[str, str] = {}
        results: list[JobRun] = []
        for job in ordered:
            blocked = self._blocked_by(job, all_jobs, cycle_status)
            if blocked:
                run = self._skip(job, current, f"dependency_not_satisfied:{blocked}")
                cycle_status[job.id] = RUN_SKIPPED
            else:
                run = self._run_job(job, current)
                cycle_status[job.id] = run.status
            results.append(run)
        return results

    def _blocked_by(self, job: RecurringJob, all_jobs: dict[str, RecurringJob],
                    cycle_status: dict[str, str]) -> str:
        for dep_id in job.dependencies:
            dep = all_jobs.get(dep_id)
            if dep is None:
                continue  # unknown dependency -> treated as satisfied
            if dep_id in cycle_status:
                if cycle_status[dep_id] != RUN_SUCCESS:
                    return dep_id
            elif dep.last_status != RUN_SUCCESS:
                return dep_id
        return ""

    def _run_job(self, job: RecurringJob, now: datetime) -> JobRun:
        started = utc_now()
        queue_job_id = ""
        try:
            queued = self.jobs.add_job(job.kind, job.name, payload=dict(job.payload))
            queue_job_id = getattr(queued, "id", "")
        except Exception:
            pass
        handler = self.handlers.get(job.name) or self.handlers.get(job.kind)
        status = RUN_SUCCESS
        output: Any = {"enqueued": queue_job_id}
        error = ""
        if handler is not None:
            try:
                output = handler(self, job)
            except Exception as exc:  # noqa: BLE001
                status = RUN_FAILED
                error = str(exc)
        job.last_run_at = now.isoformat(timespec="seconds")
        job.last_status = status
        job.run_count += 1
        self.store.upsert(job)
        run = JobRun(run_id=new_id("run"), job_id=job.id, name=job.name, status=status,
                     started_at=started, ended_at=utc_now(), output=output, error=error,
                     queue_job_id=queue_job_id)
        return self.store.append_run(run)

    def _skip(self, job: RecurringJob, now: datetime, reason: str) -> JobRun:
        run = JobRun(run_id=new_id("run"), job_id=job.id, name=job.name, status=RUN_SKIPPED,
                     started_at=utc_now(), ended_at=utc_now(), error=reason)
        return self.store.append_run(run)

    # -- dependency ordering ----------------------------------------------
    @staticmethod
    def _topological(jobs: list[RecurringJob], all_jobs: dict[str, RecurringJob]) -> list[RecurringJob]:
        due_ids = {j.id for j in jobs}
        ordered: list[RecurringJob] = []
        seen: set[str] = set()
        temp: set[str] = set()
        by_id = {j.id: j for j in jobs}

        def visit(job: RecurringJob) -> None:
            if job.id in seen:
                return
            if job.id in temp:
                return  # cycle guard: break gracefully
            temp.add(job.id)
            for dep_id in job.dependencies:
                if dep_id in due_ids and dep_id != job.id:
                    visit(by_id[dep_id])
            temp.discard(job.id)
            seen.add(job.id)
            ordered.append(job)

        for job in jobs:
            visit(job)
        return ordered
