"""v30.69 Multi-Agent Coordination.

Orchestrates the EXISTING agents (Planner, Workflow Executor, Memory, Goals,
Reasoning, Job Queue) as specialists behind one Coordinator - no second agent
engine. Provides a communication bus, capability-based task delegation and
shared context/memory/goals.

Public surface:
    Coordinator, CoordinationWorkspace
    CommunicationBus
    SharedContext, SharedMemory, SharedGoals
    SpecialistAgent + PlannerAgent, CriticAgent, ReviewerAgent, ExecutorAgent,
        MemoryAgent, SearchAgent, ImportAgent
    AgentTask, AgentResult, AgentMessage
"""

from __future__ import annotations

from .agents import (
    CriticAgent,
    ExecutorAgent,
    ImportAgent,
    MemoryAgent,
    PlannerAgent,
    ReviewerAgent,
    SearchAgent,
    SpecialistAgent,
    default_agents,
)
from .bus import CommunicationBus
from .coordinator import CoordinationWorkspace, Coordinator
from .models import AgentMessage, AgentResult, AgentTask
from .shared import SharedContext, SharedGoals, SharedMemory

__all__ = [
    "Coordinator",
    "CoordinationWorkspace",
    "CommunicationBus",
    "SharedContext",
    "SharedMemory",
    "SharedGoals",
    "SpecialistAgent",
    "PlannerAgent",
    "CriticAgent",
    "ReviewerAgent",
    "ExecutorAgent",
    "MemoryAgent",
    "SearchAgent",
    "ImportAgent",
    "default_agents",
    "AgentTask",
    "AgentResult",
    "AgentMessage",
]
