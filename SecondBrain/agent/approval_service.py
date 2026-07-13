from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.events.domain_events import (
    AgentPlanPaused,
    AgentPlanRejected,
    AgentPlanResumed,
    ApprovalApproved,
    ApprovalDeferred,
    ApprovalRejected,
    ApprovalRequested,
    DomainEvent,
    sanitize_metadata,
)
from secondbrain.events.event_bus import EventBus
from secondbrain.native.approval import NativeApprovalQueue

from .approval_bridge import AgentApprovalBridge
from .plan_store import AgentPlanStore
from .task_planner import TaskStepState
from .tool_registry import ToolDefinition


class AgentApprovalService:
    """Validated decision lifecycle for approvals created by agent plans."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        queue: NativeApprovalQueue | None = None,
        bridge: AgentApprovalBridge | None = None,
        plan_store: AgentPlanStore | None = None,
        event_bus: EventBus | None = None,
        repository: Any | None = None,
    ) -> None:
        if queue is not None and bridge is not None and queue.path != bridge.queue.path:
            raise ValueError("approval_queue_mismatch")
        # A repository lets the service run over the persistence abstraction; the
        # JSONL repository exposes the native queue, so existing logic is reused.
        if repository is not None and queue is None and getattr(repository, "queue", None) is not None:
            queue = repository.queue
        self.queue = queue or (bridge.queue if bridge is not None else NativeApprovalQueue(project_root or Path.cwd()))
        self.bridge = bridge or AgentApprovalBridge(queue=self.queue)
        self.plan_store = plan_store
        self.event_bus = event_bus or EventBus()
        self.repository = repository
        self._correlation_ids: dict[str, str] = {}

    def create_approval(
        self,
        *,
        plan_id: str,
        step_id: str,
        tool: ToolDefinition,
        intent: str,
        payload: Mapping[str, Any],
        workspace_id: str | None = None,
        create_review: bool = False,
        review_title: str = "",
        review_description: str = "",
        review_source: str = "agent",
        review_category: str | None = None,
        actor: str = "agent_executor",
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        """Create through the existing bridge and publish only sanitized event metadata."""

        approval = self.bridge.create_approval(
            plan_id=plan_id,
            step_id=step_id,
            tool=tool,
            intent=intent,
            payload=payload,
            workspace_id=workspace_id,
            create_review=create_review,
            review_title=review_title,
            review_description=review_description,
            review_source=review_source,
            review_category=review_category,
        )
        approval_id = str(approval["approval_id"])
        correlation = correlation_id or plan_id or approval_id
        self._correlation_ids[approval_id] = correlation
        requested = ApprovalRequested(
            workspace_id=workspace_id or "",
            actor=actor,
            correlation_id=correlation,
            causation_id=causation_id,
            item_id=approval_id,
            plan_id=plan_id,
            step_id=step_id,
            category=str(approval.get("category") or "risky_agent_action"),
            sanitized_metadata={
                "tool_name": tool.name,
                "intent": intent,
                "risk_level": tool.risk_level.value,
                "status": str(approval.get("status") or "pending"),
            },
        )
        self.event_bus.publish(requested)
        self.event_bus.publish(self._plan_event(AgentPlanPaused, approval, actor, correlation, requested.event_id))
        return approval

    def request_approval(self, **kwargs: Any) -> dict[str, Any]:
        return self.create_approval(**kwargs)

    def create(self, **kwargs: Any) -> dict[str, Any]:
        return self.create_approval(**kwargs)

    def create_connector_approval(
        self,
        *,
        connector_id: str,
        workspace_id: str,
        action: str,
        actor: str,
        binding: Mapping[str, Any],
        risk_level: str = "high",
        expires_at: float,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        """Create a connector-bound approval in the shared native queue."""

        safe_binding = sanitize_metadata(binding)
        safe_binding.update(
            connector_id=connector_id,
            workspace_id=workspace_id,
            action=action,
            actor=actor,
            expires_at=float(expires_at),
        )
        approval = self.queue.create(
            command=f"connector.{action}",
            intent=action,
            text=f"Connector action requires approval: {action}",
            target=connector_id,
            risk_level=risk_level,
            reason="Connector permission or external write requires explicit approval.",
            category="connector_permission_change",
            tool_name=f"connector.{action}",
            payload=safe_binding,
            workspace_id=workspace_id,
        )
        approval_id = str(approval["approval_id"])
        correlation = correlation_id or f"connector:{workspace_id}:{connector_id}:{action}"
        self._correlation_ids[approval_id] = correlation
        self.event_bus.publish(
            ApprovalRequested(
                workspace_id=workspace_id,
                actor=actor,
                correlation_id=correlation,
                causation_id=causation_id,
                item_id=approval_id,
                category="connector_permission_change",
                sanitized_metadata={
                    "connector_id": connector_id,
                    "action": action,
                    "risk_level": risk_level,
                    "expires_at": float(expires_at),
                    **safe_binding,
                },
            )
        )
        return approval

    def approve(
        self,
        approval_id: str,
        actor: str,
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._decide(
            approval_id,
            "approved",
            actor=actor,
            note=note,
            correlation_id=correlation_id,
            causation_id=causation_id,
            expected_version=expected_version,
        )

    def reject(
        self,
        approval_id: str,
        actor: str,
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._decide(
            approval_id,
            "rejected",
            actor=actor,
            note=note,
            correlation_id=correlation_id,
            causation_id=causation_id,
            expected_version=expected_version,
        )

    def defer(
        self,
        approval_id: str,
        actor: str,
        until: str = "",
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        return self._decide(
            approval_id,
            "deferred",
            actor=actor,
            note=note,
            deferred_until=until,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def begin_execution(
        self,
        approval_id: str,
        *,
        executor_id: str,
        lease_seconds: int = 300,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self.queue.begin_execution(
            approval_id,
            executor_id=executor_id,
            lease_seconds=lease_seconds,
            expected_version=expected_version,
        )

    def complete_execution(
        self,
        approval_id: str,
        *,
        execution_token: str,
        expected_version: int | None = None,
        result_status: str = "completed",
    ) -> dict[str, Any]:
        return self.queue.complete_execution(
            approval_id,
            execution_token=execution_token,
            expected_version=expected_version,
            result_status=result_status,
        )

    def recover_stale_leases(self) -> list[dict[str, Any]]:
        return self.queue.recover_stale_leases()

    def health(self) -> dict[str, Any]:
        if self.repository is not None:
            return self.repository.health().to_dict()
        return {"backend": "jsonl", "healthy": True, "degraded": False, "detail": "native queue"}

    def get(self, approval_id: str) -> dict[str, Any] | None:
        return self.queue.get(approval_id)

    def list_pending(self) -> list[dict[str, Any]]:
        return self.queue.list(status="pending")

    def list_by_plan(self, plan_id: str) -> list[dict[str, Any]]:
        return [row for row in self.queue.list() if row.get("plan_id") == plan_id]

    def _decide(
        self,
        approval_id: str,
        status: str,
        *,
        actor: str,
        note: str,
        deferred_until: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        step_state = self.bridge.step_state_for_status(status)
        updated = self.queue.transition(
            approval_id,
            status,
            actor=actor,
            note=note,
            deferred_until=deferred_until,
            step_state=step_state.value,
            expected_version=expected_version,
        )
        if updated is None:
            raise KeyError(f"approval_not_found:{approval_id}")
        self._sync_plan(updated)
        self._publish_decision(
            updated,
            actor=actor,
            note=note,
            deferred_until=deferred_until,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        return updated

    def _publish_decision(
        self,
        approval: dict[str, Any],
        *,
        actor: str,
        note: str,
        deferred_until: str,
        correlation_id: str,
        causation_id: str,
    ) -> None:
        status = str(approval.get("status") or "")
        event_types: dict[str, tuple[type[DomainEvent], type[DomainEvent]]] = {
            "approved": (ApprovalApproved, AgentPlanResumed),
            "rejected": (ApprovalRejected, AgentPlanRejected),
            "deferred": (ApprovalDeferred, AgentPlanPaused),
        }
        approval_event_type, plan_event_type = event_types[status]
        approval_id = str(approval.get("approval_id") or "")
        correlation = (
            correlation_id
            or self._correlation_ids.get(approval_id)
            or str(approval.get("plan_id") or "")
            or approval_id
        )
        self._correlation_ids[approval_id] = correlation
        event = approval_event_type(
            workspace_id=str(approval.get("workspace_id") or ""),
            actor=actor,
            correlation_id=correlation,
            causation_id=causation_id,
            item_id=approval_id,
            plan_id=str(approval.get("plan_id") or ""),
            step_id=str(approval.get("step_id") or ""),
            category=str(approval.get("category") or "risky_agent_action"),
            sanitized_metadata={
                "tool_name": str(approval.get("tool_name") or approval.get("command") or ""),
                "status": status,
                "decision_note": note,
                "deferred_until": deferred_until,
            },
        )
        self.event_bus.publish(event)
        if approval.get("plan_id"):
            self.event_bus.publish(self._plan_event(plan_event_type, approval, actor, correlation, event.event_id))

    @staticmethod
    def _plan_event(
        event_type: type[DomainEvent],
        approval: Mapping[str, Any],
        actor: str,
        correlation_id: str,
        causation_id: str,
    ) -> DomainEvent:
        return event_type(
            workspace_id=str(approval.get("workspace_id") or ""),
            actor=actor,
            correlation_id=correlation_id,
            causation_id=causation_id,
            item_id=str(approval.get("approval_id") or ""),
            plan_id=str(approval.get("plan_id") or ""),
            step_id=str(approval.get("step_id") or ""),
            category=str(approval.get("category") or "risky_agent_action"),
            sanitized_metadata={
                "approval_status": str(approval.get("status") or "pending"),
                "tool_name": str(approval.get("tool_name") or approval.get("command") or ""),
            },
        )

    def _sync_plan(self, approval: dict[str, Any]) -> None:
        if self.plan_store is None or not approval.get("plan_id") or not approval.get("step_id"):
            return
        try:
            plan = self.plan_store.load(str(approval["plan_id"]))
        except KeyError:
            return
        step = next((item for item in plan.steps if item.step_id == approval["step_id"]), None)
        if step is None or step.state == TaskStepState.COMPLETED:
            return
        status = str(approval.get("status") or "")
        step.state = self.bridge.step_state_for_status(status)
        plan.metadata["status"] = "rejected" if status == "rejected" else "waiting_for_approval"
        self.plan_store.update(plan)
