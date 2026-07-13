from __future__ import annotations

import json
from pathlib import Path

from .connector_job_models import ConnectorJob


class ConnectorJobHistory:
    def __init__(self, path: str | Path | None = None, *, max_entries: int = 200) -> None:
        self.path = Path(path) if path else None
        self.max_entries = max_entries
        self._jobs: list[ConnectorJob] = []

    def add(self, job: ConnectorJob) -> None:
        self._jobs.append(job)
        self._jobs = self._jobs[-self.max_entries :]
        self.save()

    def list(self, *, connector_id: str | None = None) -> list[ConnectorJob]:
        jobs = self._jobs
        if connector_id:
            jobs = [job for job in jobs if job.connector_id == connector_id]
        return list(jobs)

    def last_for(self, connector_id: str) -> ConnectorJob | None:
        matches = self.list(connector_id=connector_id)
        return matches[-1] if matches else None

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [job.to_dict() for job in self._jobs]
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
