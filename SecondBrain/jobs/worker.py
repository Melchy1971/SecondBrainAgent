"""Worker and handler registries for the central persistent job runtime."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from threading import Event, Lock
from typing import Any, Callable

from secondbrain.jobs.models import Job, JobStatus

JobHandler = Callable[[Job, "JobContext"], Any]


class JobHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_type: str, handler: JobHandler) -> None:
        if job_type in self._handlers:
            raise ValueError(f"handler_already_registered:{job_type}")
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> JobHandler:
        try:
            return self._handlers[job_type]
        except KeyError as exc:
            raise LookupError(f"missing_job_handler:{job_type}") from exc


class WorkerRegistry:
    def __init__(self) -> None:
        self._health: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def heartbeat(self, worker_id: str, *, active: int = 0, state: str = "healthy") -> None:
        from datetime import datetime, timezone
        with self._lock:
            self._health[worker_id] = {
                "worker_id": worker_id, "state": state, "active": active,
                "heartbeat_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }

    def unregister(self, worker_id: str) -> None:
        with self._lock:
            self._health.pop(worker_id, None)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self._health.values()]


@dataclass
class JobContext:
    repository: Any
    job: Job
    worker_id: str
    stop_event: Event

    def heartbeat(self) -> None:
        self.job = self.repository.renew_lease(
            self.job.job_id, workspace_id=self.job.workspace_id, worker_id=self.worker_id)

    def checkpoint(self, data: dict[str, Any], *, progress: float | None = None) -> None:
        self.job = self.repository.save_checkpoint(
            self.job.job_id, workspace_id=self.job.workspace_id,
            worker_id=self.worker_id, checkpoint=data)
        if progress is not None:
            self.job = self.repository.update_progress(
                self.job.job_id, workspace_id=self.job.workspace_id,
                worker_id=self.worker_id, progress=progress)

    @property
    def cancelled(self) -> bool:
        current = self.repository.get_job(self.job.job_id, workspace_id=self.job.workspace_id)
        return self.stop_event.is_set() or current is None or current.status == JobStatus.CANCELLED.value


class JobWorker:
    def __init__(self, repository: Any, handlers: JobHandlerRegistry, *, worker_id: str,
                 workspace_id: str, registry: WorkerRegistry | None = None,
                 parallelism: int = 1, timeout_seconds: float = 300.0) -> None:
        self.repository = repository
        self.handlers = handlers
        self.worker_id = worker_id
        self.workspace_id = workspace_id
        self.registry = registry or WorkerRegistry()
        self.parallelism = max(1, int(parallelism))
        self.timeout_seconds = max(0.01, float(timeout_seconds))
        self._stop = Event()

    def run_once(self) -> Job | None:
        if self._stop.is_set():
            return None
        job = self.repository.claim_next_job(worker_id=self.worker_id, workspace_id=self.workspace_id)
        if job is None:
            self.registry.heartbeat(self.worker_id, active=0)
            return None
        job = self.repository.start_job(job.job_id, workspace_id=job.workspace_id, worker_id=self.worker_id)
        self.registry.heartbeat(self.worker_id, active=1)
        context = JobContext(self.repository, job, self.worker_id, self._stop)
        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"job-{self.worker_id}")
        future = pool.submit(self.handlers.get(job.type), job, context)
        try:
            future.result(timeout=self.timeout_seconds)
        except TimeoutError:
            self._stop.set()
            job = self.repository.fail_job(
                job.job_id, workspace_id=job.workspace_id, worker_id=self.worker_id,
                error_code="job_timeout", error_summary="handler exceeded configured timeout")
        except Exception as exc:  # noqa: BLE001
            job = self.repository.fail_job(
                job.job_id, workspace_id=job.workspace_id, worker_id=self.worker_id,
                error_code="job_handler_failed", error_summary=type(exc).__name__)
        else:
            current = self.repository.get_job(job.job_id, workspace_id=job.workspace_id)
            if current is not None and current.status == JobStatus.CANCELLED.value:
                job = current
            else:
                job = self.repository.complete_job(
                    job.job_id, workspace_id=job.workspace_id, worker_id=self.worker_id)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
            self.registry.heartbeat(self.worker_id, active=0)
        return job

    def run_batch(self) -> list[Job]:
        results: list[Job] = []
        for _ in range(self.parallelism):
            job = self.run_once()
            if job is None:
                break
            results.append(job)
        return results

    def shutdown(self) -> None:
        self._stop.set()
        self.registry.unregister(self.worker_id)
