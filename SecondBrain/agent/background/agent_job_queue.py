from __future__ import annotations

from collections import deque
from .agent_job import AgentJob


class AgentJobQueue:
    def __init__(self) -> None:
        self._queue: deque[AgentJob] = deque()

    def enqueue(self, job: AgentJob) -> AgentJob:
        job.mark_queued()
        self._queue.append(job)
        return job

    def dequeue(self) -> AgentJob | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def remove(self, job_id: str) -> bool:
        for job in list(self._queue):
            if job.job_id == job_id:
                self._queue.remove(job)
                return True
        return False

    def __len__(self) -> int:
        return len(self._queue)

    def list_jobs(self) -> list[AgentJob]:
        return list(self._queue)
