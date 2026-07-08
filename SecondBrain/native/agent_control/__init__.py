"""v30.66 Native Agent Control.

The single agent-control surface inside the native AI Workspace. Aggregates the
existing agent subsystems (Planner, Workflow Engine, Background Agents,
Approval/Safety layer, Goal Tracking) plus audit and logs into GUI areas -
no second GUI, no second engine.
"""

from __future__ import annotations

from .service import AREAS, AgentControlService

__all__ = ["AgentControlService", "AREAS"]
