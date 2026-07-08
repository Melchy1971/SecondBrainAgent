from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .agent_job import AgentJob, AgentJobResult
from .agent_job_events import AgentJobEvent, AgentJobEventBus, AgentJobEventType
from .agent_retry_policy import AgentRetryPolicy

PlanExecutor = Callable[[AgentJob], AgentJobResult | Any]


class AgentJobRunner:
    def __init__(self, executor: PlanExecutor, retry_policy: AgentRetryPolicy | None = None, event_bus: AgentJobEventBus | None = None) -> None:
        self.executor = executor
        self.retry_policy = retry_policy or AgentRetryPolicy(max_attempts=1)
        self.event_bus = event_bus or AgentJobEventBus()

    def run(self, job: AgentJob) -> AgentJob:
        while True:
            try:
                job.mark_running()
                self.event_bus.publish(AgentJobEvent(AgentJobEventType.STARTED, job.job_id, job.plan_id))
                raw = self.executor(job)
                result = raw if isinstance(raw, AgentJobResult) else AgentJobResult(success=True, output=raw)
                if result.success:
                    job.mark_completed(result)
                    self.event_bus.publish(AgentJobEvent(AgentJobEventType.COMPLETED, job.job_id, job.plan_id, payload={'progress': job.progress}))
                    return job
                raise RuntimeError(result.error or 'agent job failed')
            except BaseException as exc:
                job.mark_failed(str(exc))
                self.event_bus.publish(AgentJobEvent(AgentJobEventType.FAILED, job.job_id, job.plan_id, payload={'error': str(exc)}))
                if self.retry_policy.should_retry(job.attempt, exc):
                    job.status = job.status.RETRYING
                    self.event_bus.publish(AgentJobEvent(AgentJobEventType.RETRYING, job.job_id, job.plan_id, payload={'attempt': job.attempt + 1}))
                    continue
                return job
