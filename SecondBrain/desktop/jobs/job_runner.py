from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .job_state import DesktopJob
from .job_registry import JobRegistry

EventEmitter = Callable[[str, dict[str, Any]], None]


def noop_emit(event_name: str, payload: dict[str, Any]) -> None:
    return None


@dataclass
class JobRunner:
    registry: JobRegistry
    emit: EventEmitter = noop_emit

    def run(self, job: DesktopJob) -> DesktopJob:
        registered = self.registry.get(job.name)
        self.emit("JOB_STARTED", {"job_id": job.job_id, "name": job.name})
        job.mark_running()
        try:
            result = registered.handler(job.metadata)
            if isinstance(result, dict):
                job.metadata.update(result)
            job.mark_completed()
            self.emit("JOB_COMPLETED", {"job_id": job.job_id, "name": job.name})
        except TimeoutError as exc:
            job.mark_timeout(str(exc) or "job timeout")
            self.emit("JOB_FAILED", {"job_id": job.job_id, "name": job.name, "error": job.error, "state": job.state.value})
        except Exception as exc:
            job.mark_failed(str(exc))
            self.emit("JOB_FAILED", {"job_id": job.job_id, "name": job.name, "error": job.error})
        return job
