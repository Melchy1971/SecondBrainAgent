from __future__ import annotations

from collections.abc import Callable
from .agent_job import AgentJob, AgentJobResult, AgentJobStatus
from .agent_job_events import AgentJobEvent, AgentJobEventBus, AgentJobEventType
from .agent_job_history import AgentJobHistory
from .agent_job_queue import AgentJobQueue
from .agent_job_runner import AgentJobRunner
from .agent_retry_policy import AgentRetryPolicy


class AgentJobManager:
    def __init__(self, executor: Callable[[AgentJob], AgentJobResult | object], retry_policy: AgentRetryPolicy | None = None) -> None:
        self.event_bus = AgentJobEventBus()
        self.queue = AgentJobQueue()
        self.history = AgentJobHistory()
        self.runner = AgentJobRunner(executor, retry_policy=retry_policy, event_bus=self.event_bus)
        self.active: dict[str, AgentJob] = {}

    def submit(self, title: str, plan_id: str, *, max_attempts: int = 1) -> AgentJob:
        job = AgentJob(title=title, plan_id=plan_id, max_attempts=max_attempts)
        self.event_bus.publish(AgentJobEvent(AgentJobEventType.CREATED, job.job_id, job.plan_id))
        self.queue.enqueue(job)
        self.event_bus.publish(AgentJobEvent(AgentJobEventType.QUEUED, job.job_id, job.plan_id))
        return job

    def run_next(self) -> AgentJob | None:
        job = self.queue.dequeue()
        if job is None:
            return None
        self.active[job.job_id] = job
        finished = self.runner.run(job)
        self.active.pop(job.job_id, None)
        self.history.add(finished)
        return finished

    def cancel_queued(self, job_id: str, reason: str = 'cancelled') -> bool:
        for job in self.queue.list_jobs():
            if job.job_id == job_id:
                self.queue.remove(job_id)
                job.mark_cancelled(reason)
                self.history.add(job)
                self.event_bus.publish(AgentJobEvent(AgentJobEventType.CANCELLED, job.job_id, job.plan_id, payload={'reason': reason}))
                return True
        return False

    def snapshot(self) -> dict[str, int]:
        history = self.history.list()
        return {
            'queued': len(self.queue),
            'active': len(self.active),
            'completed': sum(1 for job in history if job.status == AgentJobStatus.COMPLETED),
            'failed': sum(1 for job in history if job.status == AgentJobStatus.FAILED),
            'cancelled': sum(1 for job in history if job.status == AgentJobStatus.CANCELLED),
        }
