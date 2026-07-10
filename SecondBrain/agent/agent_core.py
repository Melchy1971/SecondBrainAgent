from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .intent_router import IntentRouter
from .safe_executor import SafeExecutor
from .task_planner import TaskPlan, TaskPlanner
from .tool_discovery import ToolDiscovery
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
        if registry is None:
            runtime_root = Path.cwd() / "runtime"
            self.registry = ToolRegistry(runtime_root)
            ToolDiscovery(Path.cwd(), self.registry).discover()
        else:
            self.registry = registry
        self.executor = SafeExecutor(self.registry)

    def handle(self, request: AgentRequest) -> AgentResponse:
        route = self.router.route(request.text)
        if route.tool_name:
            plan = self.planner.create_single_tool_plan(intent=route.intent, tool_name=route.tool_name, payload=dict(route.parameters))
        else:
            plan = self.planner.create_chat_plan(text=request.text)
        self._decorate_plan_with_tools(plan)
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

    def _decorate_plan_with_tools(self, plan: TaskPlan) -> None:
        used_tools: list[dict[str, Any]] = []
        for step in plan.steps:
            if not step.tool_name:
                continue
            try:
                definition = self.registry.get(step.tool_name)
            except Exception:  # noqa: BLE001 - plan decoration must not block execution
                continue
            contract = {
                "name": definition.name,
                "category": definition.category,
                "risk_level": definition.risk_level.value,
                "requires_approval": definition.requires_approval,
                "timeout_seconds": definition.timeout_seconds,
                "retry_count": definition.retry_count,
                "input_schema": definition.input_schema.to_dict(),
                "output_schema": dict(definition.output_schema),
            }
            step.tool_contract = contract
            used_tools.append(contract)
        if used_tools:
            plan.metadata["used_tools"] = used_tools
