from __future__ import annotations

from .connector_job_history import ConnectorJobHistory
from .connector_job_models import ConnectorJob, ConnectorJobResult
from .connector_job_monitor import ConnectorJobMonitor, ConnectorJobSnapshot
from .connector_job_runner import ConnectorJobRunner


class ConnectorJobService:
    def __init__(
        self,
        runner: ConnectorJobRunner | None = None,
        history: ConnectorJobHistory | None = None,
        monitor: ConnectorJobMonitor | None = None,
    ) -> None:
        self.runner = runner or ConnectorJobRunner()
        self.history = history or ConnectorJobHistory()
        self.monitor = monitor or ConnectorJobMonitor(self.history)
        self._active: dict[str, ConnectorJob] = {}

    def create_sync_job(self, connector_id: str, *, cursor_before: str | None = None) -> ConnectorJob:
        job = ConnectorJob.create(connector_id, cursor_before=cursor_before).queued()
        self._active[job.job_id] = job
        return job

    def run(self, job_id: str) -> ConnectorJobResult:
        job = self._active.get(job_id)
        if job is None:
            raise KeyError(f"unknown connector job: {job_id}")
        result_job = self.runner.run_sync(job)
        self._active.pop(job_id, None)
        self.history.add(result_job)
        return ConnectorJobResult(job=result_job, accepted=result_job.error is None, message=result_job.error or "completed")

    def cancel(self, job_id: str, reason: str = "cancelled") -> ConnectorJob:
        job = self._active.pop(job_id)
        cancelled = job.cancelled(reason)
        self.history.add(cancelled)
        return cancelled

    def active_jobs(self) -> list[ConnectorJob]:
        return list(self._active.values())

    def snapshot(self, *, connector_id: str | None = None) -> ConnectorJobSnapshot:
        return self.monitor.snapshot(connector_id=connector_id, active_jobs=self.active_jobs())
