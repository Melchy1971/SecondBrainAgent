from __future__ import annotations

from pathlib import Path
from typing import Any

from secondbrain.native.approval import NativeApprovalQueue

from .approval_bridge import AgentApprovalBridge
from .plan_store import AgentPlanStore
from .task_planner import TaskStepState


class AgentApprovalService:
    """Validated decision lifecycle for approvals created by agent plans."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        queue: NativeApprovalQueue | None = None,
        bridge: AgentApprovalBridge | None = None,
        plan_store: AgentPlanStore | None = None,
    ) -> None:
        if queue is not None and bridge is not None and queue.path != bridge.queue.path:
            raise ValueError("approval_queue_mismatch")
        self.queue = queue or (bridge.queue if bridge is not None else NativeApprovalQueue(project_root or Path.cwd()))
        self.bridge = bridge or AgentApprovalBridge(queue=self.queue)
        self.plan_store = plan_store

    def approve(self, approval_id: str, actor: str, note: str = "") -> dict[str, Any]:
        return self._decide(approval_id, "approved", actor=actor, note=note)

    def reject(self, approval_id: str, actor: str, note: str = "") -> dict[str, Any]:
        return self._decide(approval_id, "rejected", actor=actor, note=note)

    def defer(
        self,
        approval_id: str,
        actor: str,
        until: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        return self._decide(
            approval_id,
            "deferred",
            actor=actor,
            note=note,
            deferred_until=until,
        )

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
    ) -> dict[str, Any]:
        step_state = self.bridge.step_state_for_status(status)
        updated = self.queue.transition(
            approval_id,
            status,
            actor=actor,
            note=note,
            deferred_until=deferred_until,
            step_state=step_state.value,
        )
        if updated is None:
            raise KeyError(f"approval_not_found:{approval_id}")
        self._sync_plan(updated)
        return updated

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
