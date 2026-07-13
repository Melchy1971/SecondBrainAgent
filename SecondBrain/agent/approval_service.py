from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from threading import local
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
from secondbrain.native.approval import ApprovalConcurrencyError, NativeApprovalQueue
from secondbrain.repositories.jsonl_review_approval_repository import (
    JsonlReviewApprovalRepository,
)
from secondbrain.repositories.review_approval_repository import (
    RepositoryConflict,
    create_review_approval_repository,
)

from .approval_bridge import AgentApprovalBridge
from .plan_store import AgentPlanStore
from .task_planner import TaskStepState
from .tool_registry import ToolDefinition


class _RepositoryApprovalQueue:
    """Native-queue compatible facade used by agent components on PostgreSQL."""

    def __init__(self, repository: Any, project_root: Path) -> None:
        self.repository = repository
        self.project_root = project_root
        self.path = project_root / "runtime" / "agent" / "repository-approvals"
        self._execution_context = local()

    def create(self, **fields: Any) -> dict[str, Any]:
        return self.repository.create_approval(**fields)

    def get(self, approval_id: str) -> dict[str, Any] | None:
        item = self.repository.get_item(approval_id)
        if item is None or not item.get("approval_id"):
            return None
        authorized = getattr(self._execution_context, "authorized", {})
        token = authorized.get(approval_id) if isinstance(authorized, dict) else None
        if token and item.get("status") == "executing" and item.get("lease_id") == token:
            return {**item, "status": "approved"}
        return item

    def list(self, *, status: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_items(item_type="approval", status=status)

    def transition(self, approval_id: str, new_status: str, **fields: Any):
        fields.pop("step_state", None)
        try:
            return self.repository.update_status(approval_id, new_status, **fields)
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def begin_execution(self, approval_id: str, **fields: Any) -> dict[str, Any]:
        try:
            return self.repository.acquire_execution_lease(approval_id, **fields)
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def heartbeat_execution(
        self, approval_id: str, *, lease_id: str, lease_seconds: int = 300
    ) -> dict[str, Any]:
        try:
            return self.repository.renew_execution_lease(
                approval_id,
                execution_token=lease_id,
                lease_seconds=lease_seconds,
            )
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def complete_execution(self, approval_id: str, **fields: Any) -> dict[str, Any]:
        return self.repository.release_execution_lease(approval_id, **fields)

    @contextmanager
    def execution_authorization(self, approval_id: str, lease_id: str):
        item = self.repository.get_item(approval_id)
        if (
            item is None
            or item.get("status") != "executing"
            or item.get("lease_id") != lease_id
        ):
            raise ApprovalConcurrencyError(f"execution_lease_mismatch:{approval_id}")
        previous = getattr(self._execution_context, "authorized", {})
        self._execution_context.authorized = {**previous, approval_id: lease_id}
        try:
            yield
        finally:
            self._execution_context.authorized = previous

    def link_review(self, approval_id: str, review_id: str) -> dict[str, Any]:
        item = self.get(approval_id)
        if item is None:
            raise KeyError(f"approval_not_found:{approval_id}")
        return {**item, "review_id": review_id}

    def recover_stale_leases(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        return []


class _RepositoryReviewQueue:
    def __init__(self, repository: Any, project_root: Path) -> None:
        self.repository = repository
        self.project_root = project_root
        self.path = project_root / "runtime" / "agent" / "repository-reviews"

    def create(self, **fields: Any) -> dict[str, Any]:
        return self.repository.create_review(**fields)

    def get(self, review_id: str) -> dict[str, Any] | None:
        item = self.repository.get_item(review_id)
        return item if item is not None and item.get("review_id") else None

    def list(
        self, *, status: str | None = None, category: str | None = None
    ) -> list[dict[str, Any]]:
        items = self.repository.list_items(item_type="review", status=status)
        return [item for item in items if category is None or item.get("category") == category]


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
        selected_queue = queue or (bridge.queue if bridge is not None else None)
        root = Path(
            project_root
            or (selected_queue.project_root if selected_queue is not None else Path.cwd())
        ).resolve()
        if repository is None:
            if selected_queue is not None:
                repository = JsonlReviewApprovalRepository(root)
                repository.queue = selected_queue
                if bridge is not None:
                    repository.reviews = bridge.review_queue
            else:
                repository = create_review_approval_repository(root)
        repository_queue = getattr(repository, "queue", None)
        # Keep the historical queue attribute for callers that inspect the native
        # JSONL queue. Persistence operations below always use the repository.
        self.queue = selected_queue or repository_queue or _RepositoryApprovalQueue(
            repository, root
        )
        self.bridge = bridge or AgentApprovalBridge(
            queue=self.queue,
            review_queue=(
                getattr(repository, "reviews", None)
                or _RepositoryReviewQueue(repository, root)
            ),
        )
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
        """Create via the configured repository and publish sanitized metadata."""

        category = self.bridge.category_for(
            tool.name, intent=intent, tool_category=tool.category
        )
        safe_payload = tool.input_schema.sanitize(payload)
        approval = self.repository.create_approval(
            command=tool.name,
            intent=intent,
            text=f"Agent step requires approval: {tool.name}",
            target=step_id,
            risk_level=tool.risk_level.value,
            reason="Agent tool execution requires explicit approval.",
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool.name,
            payload=safe_payload,
            workspace_id=workspace_id,
            step_state=TaskStepState.WAITING_FOR_APPROVAL.value,
        )
        if create_review:
            self.repository.create_review(
                category=review_category or category,
                title=review_title or f"Review required: {tool.name}",
                description=review_description or str(approval.get("reason") or ""),
                source=review_source,
                target=step_id,
                approval_id=str(approval["approval_id"]),
                workspace_id=workspace_id,
                metadata={
                    "risk_level": tool.risk_level.value,
                    "plan_id": plan_id,
                    "step_id": step_id,
                    "tool_name": tool.name,
                    "workspace_id": workspace_id or "",
                },
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
        approval_category: str = "connector_permission_change",
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        """Create a connector-bound approval in the configured repository."""

        allowed_categories = {
            "connector_permission_change", "risky_agent_action", "delete_request",
        }
        category = approval_category if approval_category in allowed_categories else "risky_agent_action"
        safe_binding = sanitize_metadata(binding)
        safe_binding.update(
            connector_id=connector_id,
            workspace_id=workspace_id,
            action=action,
            actor=actor,
            expires_at=float(expires_at),
        )
        approval = self.repository.create_approval(
            command=f"connector.{action}",
            intent=action,
            text=f"Connector action requires approval: {action}",
            target=connector_id,
            risk_level=risk_level,
            reason="Connector permission or external write requires explicit approval.",
            category=category,
            tool_name=f"connector.{action}",
            payload=safe_binding,
            workspace_id=workspace_id,
            idempotency_key=str(safe_binding.get("idempotency_key") or ""),
            tool_idempotent=False,
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
                category=category,
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
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._decide(
            approval_id,
            "deferred",
            actor=actor,
            note=note,
            deferred_until=until,
            correlation_id=correlation_id,
            causation_id=causation_id,
            expected_version=expected_version,
        )

    def begin_execution(
        self,
        approval_id: str,
        *,
        executor_id: str,
        lease_seconds: int = 300,
        expected_version: int | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        try:
            return self.repository.acquire_execution_lease(
                approval_id,
                executor_id=executor_id,
                lease_seconds=lease_seconds,
                expected_version=expected_version,
                idempotency_key=idempotency_key,
            )
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def complete_execution(
        self,
        approval_id: str,
        *,
        execution_token: str,
        expected_version: int | None = None,
        result_status: str = "completed",
        result: Any = None,
    ) -> dict[str, Any]:
        try:
            return self.repository.release_execution_lease(
                approval_id,
                execution_token=execution_token,
                expected_version=expected_version,
                result_status=result_status,
                result=result,
            )
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def heartbeat_execution(
        self,
        approval_id: str,
        *,
        lease_id: str,
        lease_seconds: int = 300,
    ) -> dict[str, Any]:
        try:
            return self.repository.renew_execution_lease(
                approval_id,
                execution_token=lease_id,
                lease_seconds=lease_seconds,
            )
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc

    def recover_stale_leases(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        recover = getattr(self.repository, "recover_stale_leases", None)
        return recover(now=now) if callable(recover) else []

    def health(self) -> dict[str, Any]:
        return self.repository.health().to_dict()

    def get(
        self, approval_id: str, *, workspace_id: str | None = None
    ) -> dict[str, Any] | None:
        item = self.repository.get_item(approval_id, workspace_id=workspace_id)
        if item is None or not item.get("approval_id"):
            return None
        return item

    def list_pending(self, *, workspace_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_items(
            item_type="approval", status="pending", workspace_id=workspace_id
        )

    def list_by_plan(
        self, plan_id: str, *, workspace_id: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            row
            for row in self.repository.list_items(
                item_type="approval", workspace_id=workspace_id
            )
            if row.get("plan_id") == plan_id
        ]

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
        try:
            updated = self.repository.update_status(
                approval_id,
                status,
                actor=actor,
                note=note,
                deferred_until=deferred_until,
                expected_version=expected_version,
            )
        except RepositoryConflict as exc:
            raise ApprovalConcurrencyError(str(exc)) from exc
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
