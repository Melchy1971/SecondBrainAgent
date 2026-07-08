from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AgentJobEventType(str, Enum):
    CREATED = 'agent_job_created'
    QUEUED = 'agent_job_queued'
    STARTED = 'agent_job_started'
    PROGRESS = 'agent_job_progress'
    COMPLETED = 'agent_job_completed'
    FAILED = 'agent_job_failed'
    CANCELLED = 'agent_job_cancelled'
    RETRYING = 'agent_job_retrying'


@dataclass(slots=True)
class AgentJobEvent:
    event_type: AgentJobEventType
    job_id: str
    plan_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)


class AgentJobEventBus:
    def __init__(self) -> None:
        self.events: list[AgentJobEvent] = []

    def publish(self, event: AgentJobEvent) -> None:
        self.events.append(event)

    def for_job(self, job_id: str) -> list[AgentJobEvent]:
        return [event for event in self.events if event.job_id == job_id]
