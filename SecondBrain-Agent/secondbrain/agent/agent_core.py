from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .intent_router import IntentRouter
from .safe_executor import SafeExecutor
from .task_planner import TaskPlan, TaskPlanner
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class AgentRequest:
    text: str
    workspace_id: str | None = None
    confirmed: bool = False
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResponse:
    ok: bool
    intent: str
    message: str
    plan: TaskPlan
    results: list[Any]
    errors: list[str]


class AgentCore:
    def __init__(self, *, router: IntentRouter | None = None, planner: TaskPlanner | None = None, registry: ToolRegistry | None = None) -> None:
        self.router = router or IntentRouter()
        self.planner = planner or TaskPlanner()
        self.registry = registry or ToolRegistry()
        self.executor = SafeExecutor(self.registry)

    def handle(self, request: AgentRequest) -> AgentResponse:
        route = self.router.route(request.text)
        if route.tool_name:
            plan = self.planner.create_single_tool_plan(intent=route.intent, tool_name=route.tool_name, payload=dict(route.parameters))
        else:
            plan = self.planner.create_chat_plan(text=request.text)
        result = self.executor.execute(plan, confirmed=request.confirmed)
        message = "completed" if result.ok else "failed"
        if route.intent == "empty":
            message = "empty_input"
        return AgentResponse(
            ok=result.ok,
            intent=route.intent,
            message=message,
            plan=plan,
            results=result.results,
            errors=result.errors,
        )
