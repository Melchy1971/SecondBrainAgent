from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from .agent_job import AgentJob


class AgentJobHistory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._jobs: list[AgentJob] = []

    def add(self, job: AgentJob) -> None:
        self._jobs.append(job)

    def list(self) -> list[AgentJob]:
        return list(self._jobs)

    def persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for job in self._jobs:
            data = asdict(job)
            data['status'] = job.status.value
            data['created_at'] = job.created_at.isoformat()
            data['started_at'] = job.started_at.isoformat() if job.started_at else None
            data['finished_at'] = job.finished_at.isoformat() if job.finished_at else None
            payload.append(data)
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
