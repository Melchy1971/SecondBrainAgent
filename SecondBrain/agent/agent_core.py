from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .approval_bridge import AgentApprovalBridge
from .approval_service import AgentApprovalService
from .intent_router import IntentRouter
from .plan_store import AgentPlanStore
from .safe_executor import ExecutionResult, SafeExecutor
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
    status: str = "completed"
    approval_ids: list[str] = field(default_factory=list)


class AgentCore:
    def __init__(
        self,
        *,
        router: IntentRouter | None = None,
        planner: TaskPlanner | None = None,
        registry: ToolRegistry | None = None,
        approval_bridge: AgentApprovalBridge | None = None,
        approval_service: AgentApprovalService | None = None,
        plan_store: AgentPlanStore | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        self.router = router or IntentRouter()
        self.planner = planner or TaskPlanner()
        self.registry = registry or ToolRegistry()
        if (
            approval_bridge is not None
            and approval_service is not None
            and approval_bridge.queue.path != approval_service.queue.path
        ):
            raise ValueError("approval_queue_mismatch")
        root = Path(
            project_root
            or (plan_store.project_root if plan_store is not None else "")
            or (approval_bridge.queue.project_root if approval_bridge is not None else "")
            or (approval_service.queue.project_root if approval_service is not None else "")
            or Path.cwd()
        ).resolve()
        self.approval_bridge = approval_bridge or (
            approval_service.bridge if approval_service is not None else AgentApprovalBridge(root)
        )
        self.plan_store = plan_store or AgentPlanStore(root, registry=self.registry)
        self.approval_service = approval_service or AgentApprovalService(
            root,
            bridge=self.approval_bridge,
            plan_store=self.plan_store,
        )
        if (
            self.approval_service.plan_store is not None
            and self.approval_service.plan_store.root != self.plan_store.root
        ):
            raise ValueError("approval_plan_store_mismatch")
        if self.approval_service.plan_store is None:
            self.approval_service.plan_store = self.plan_store
        self.executor = SafeExecutor(
            self.registry,
            approval_bridge=self.approval_bridge,
            plan_store=self.plan_store,
        )

    def handle(self, request: AgentRequest) -> AgentResponse:
        route = self.router.route(request.text)
        if route.tool_name:
            plan = self.planner.create_single_tool_plan(intent=route.intent, tool_name=route.tool_name, payload=dict(route.parameters))
        else:
            plan = self.planner.create_chat_plan(text=request.text)
        result = self.executor.execute(
            plan,
            confirmed=request.confirmed,
            workspace_id=request.workspace_id,
        )
        message = result.status
        if route.intent == "empty":
            message = "empty_input"
        return AgentResponse(
            ok=result.ok,
            intent=route.intent,
            message=message,
            plan=plan,
            results=result.results,
            errors=result.errors,
            status=result.status,
            approval_ids=result.approval_ids,
        )

    def resume_approval(self, approval_id: str) -> AgentResponse:
        result = self.executor.resume_approved(approval_id)
        plan = self.plan_store.load(result.plan_id)
        return self._response_from_execution(plan, result)

    def reject_approval(self, approval_id: str) -> AgentResponse:
        approval = self.approval_service.reject(approval_id, "agent_core")
        plan = self.plan_store.load(str(approval["plan_id"]))
        return AgentResponse(
            ok=False,
            intent=plan.intent,
            message="rejected",
            plan=plan,
            results=[],
            errors=[],
            status="rejected",
            approval_ids=[approval_id],
        )

    def defer_approval(self, approval_id: str, until: str) -> AgentResponse:
        approval = self.approval_service.defer(approval_id, "agent_core", until=until)
        plan = self.plan_store.load(str(approval["plan_id"]))
        return AgentResponse(
            ok=False,
            intent=plan.intent,
            message="waiting_for_approval",
            plan=plan,
            results=[],
            errors=[],
            status="waiting_for_approval",
            approval_ids=[approval_id],
        )

    @staticmethod
    def _response_from_execution(plan: TaskPlan, result: ExecutionResult) -> AgentResponse:
        return AgentResponse(
            ok=result.ok,
            intent=plan.intent,
            message=result.status,
            plan=plan,
            results=result.results,
            errors=result.errors,
            status=result.status,
            approval_ids=result.approval_ids,
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
