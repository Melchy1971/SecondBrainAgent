"""v30.63 Background Agents.

Registered, recurring background tasks for Jarvis (monitors and periodic
maintenance), executed through the v30.62 Workflow Engine and mirrored into the
native Job Queue, with heartbeats, a supervisor and a failure policy.

Public surface:
    BackgroundAgent, AgentType, AgentState - agent definition
    AgentSchedule                          - when an agent is due
    AgentRun                               - one execution record
    AgentHeartbeat                         - liveness
    AgentFailurePolicy                     - repeated-failure governance
    AgentSupervisor                        - registry + lifecycle + execution
"""

from __future__ import annotations

from .handlers import HANDLERS, AgentContext, get_handler
from .models import (
    AgentFailurePolicy,
    AgentHeartbeat,
    AgentRun,
    AgentSchedule,
    AgentState,
    AgentType,
    BackgroundAgent,
)
from .store import BackgroundAgentStore
from .supervisor import AgentSupervisor

__all__ = [
    "BackgroundAgent",
    "AgentType",
    "AgentState",
    "AgentSchedule",
    "AgentRun",
    "AgentHeartbeat",
    "AgentFailurePolicy",
    "AgentSupervisor",
    "BackgroundAgentStore",
    "AgentContext",
    "HANDLERS",
    "get_handler",
]
