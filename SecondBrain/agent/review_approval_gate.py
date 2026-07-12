"""Headless end-to-end gate for the review and approval workflow."""

from __future__ import annotations

import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Barrier
from typing import Any

from secondbrain.agent.agent_core import AgentCore
from secondbrain.agent.approval_bridge import AgentApprovalBridge
from secondbrain.agent.approval_service import AgentApprovalService
from secondbrain.agent.plan_store import AgentPlanStore
from secondbrain.agent.task_planner import TaskPlan, TaskStep
from secondbrain.agent.tool_registry import (
    ToolCapability,
    ToolDefinition,
    ToolInputSchema,
    ToolRegistry,
    ToolRiskLevel,
)
from secondbrain.gui.approval_inbox import ApprovalInboxViewModel, TAB_APPROVALS
from secondbrain.native.approval import NativeApprovalQueue, approval_path


PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class GateCheck:
    check_id: str
    title: str
    passed: bool
    detail: str
    hard_blocker: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = PASS if self.passed else (BLOCKED if self.hard_blocker else CONDITIONAL_PASS)
        return value


def evaluate_gate_status(checks: list[GateCheck]) -> str:
    if any(not check.passed and check.hard_blocker for check in checks):
        return BLOCKED
    if any(not check.passed for check in checks):
        return CONDITIONAL_PASS
    return PASS


class ReviewApprovalGate:
    """Run production approval components in isolated persistent runtimes."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        self._checks: list[GateCheck] = []

    def run(self) -> dict[str, Any]:
        self._checks = []
        with tempfile.TemporaryDirectory(prefix="secondbrain-review-approval-") as directory:
            root = Path(directory)
            self._run_direct_and_approval_flow(root)
            self._run_reject_flow(root)
            self._run_defer_flow(root)
            self._run_mandatory_policy_checks(root)
            self._run_redaction_check(root)
            self._run_restart_check(root)
            self._run_corrupt_queue_check(root)
            self._run_parallel_decision_check(root)

        status = evaluate_gate_status(self._checks)
        serialized = [check.to_dict() for check in self._checks]
        return {
            "schema": "secondbrain.review_approval_gate.v1",
            "status": status,
            "ok": status != BLOCKED,
            "project_root": str(self.project_root),
            "summary": {
                "total": len(serialized),
                "passed": sum(check.passed for check in self._checks),
                "conditional": sum(not check.passed and not check.hard_blocker for check in self._checks),
                "blocked": sum(not check.passed and check.hard_blocker for check in self._checks),
            },
            "checks": serialized,
            "blockers": [check.detail for check in self._checks if not check.passed and check.hard_blocker],
            "warnings": [check.detail for check in self._checks if not check.passed and not check.hard_blocker],
        }

    def _run_direct_and_approval_flow(self, root: Path) -> None:
        low_calls: list[dict[str, Any]] = []
        low_agent = self._agent(
            root / "low",
            ToolDefinition(
                "search.query",
                "Read-only search",
                category="search",
                risk_level=ToolRiskLevel.LOW,
                handler=lambda payload: low_calls.append(dict(payload)) or {"hits": 1},
            ),
        )
        low_result = low_agent.executor.execute(self._plan("low-plan", "search.query", {"query": "gate"}))
        self._record(
            "low_risk_direct",
            "Low-risk tool runs directly",
            low_result.status == "completed" and len(low_calls) == 1,
            f"status={low_result.status}; calls={len(low_calls)}",
        )

        risky_root = root / "risky"
        risky_calls: list[dict[str, Any]] = []
        risky_agent = self._agent(
            risky_root,
            ToolDefinition(
                "agent.risky_action",
                "Risky agent action",
                category="agent",
                risk_level=ToolRiskLevel.HIGH,
                requires_approval=True,
                handler=lambda payload: risky_calls.append(dict(payload)) or {"done": True},
            ),
        )
        plan = self._plan("risky-plan", "agent.risky_action", {"target": "external"})
        waiting = risky_agent.executor.execute(plan)
        approval_id = waiting.approval_ids[0] if waiting.approval_ids else ""
        self._record(
            "risky_tool_pauses",
            "Risky agent tool pauses",
            waiting.status == "waiting_for_approval" and not waiting.errors and not risky_calls,
            f"status={waiting.status}; calls={len(risky_calls)}; errors={len(waiting.errors)}",
            hard=True,
        )

        queued = risky_agent.approval_bridge.queue.get(approval_id) if approval_id else None
        plan_file = risky_agent.plan_store._path(plan.plan_id)  # noqa: SLF001 - gate verifies persistence
        self._record(
            "approval_persisted",
            "Approval and plan are persisted",
            bool(queued) and approval_path(risky_root).exists() and plan_file.exists(),
            f"approval_present={bool(queued)}; plan_present={plan_file.exists()}",
            hard=True,
        )

        view_state = ApprovalInboxViewModel(risky_root).load(TAB_APPROVALS)
        visible_ids = {item["item_id"] for item in view_state.get("items", [])}
        self._record(
            "viewmodel_visible",
            "Approval Inbox ViewModel shows approval",
            view_state.get("ok") is True and approval_id in visible_ids,
            f"view_ok={view_state.get('ok')}; visible={approval_id in visible_ids}",
        )

        if approval_id:
            risky_agent.approval_service.approve(approval_id, "gate-reviewer", note="E2E approval")
            first = risky_agent.resume_approval(approval_id)
            second = risky_agent.resume_approval(approval_id)
            executed = risky_agent.approval_bridge.queue.get(approval_id) or {}
            exactly_once = (
                first.status == "completed"
                and second.status == "completed"
                and len(risky_calls) == 1
                and executed.get("status") == "executed"
            )
        else:
            executed = {}
            exactly_once = False
        self._record(
            "approve_exactly_once",
            "Approved step executes exactly once",
            exactly_once,
            f"calls={len(risky_calls)}; approval_status={executed.get('status', 'missing')}",
            hard=True,
        )

        audit = executed.get("decision_audit") or []
        audit_ok = any(row.get("new_status") == "approved" for row in audit) and any(
            row.get("new_status") == "executed" for row in audit
        )
        self._record(
            "decision_audit",
            "Decision audit is complete",
            audit_ok,
            f"audit_events={len(audit)}",
            hard=True,
        )

    def _run_reject_flow(self, root: Path) -> None:
        calls: list[dict[str, Any]] = []
        agent = self._blocking_agent(root / "reject", "agent.reject_target", calls)
        waiting = agent.executor.execute(self._plan("reject-plan", "agent.reject_target"))
        approval_id = waiting.approval_ids[0] if waiting.approval_ids else ""
        response = agent.reject_approval(approval_id) if approval_id else None
        persisted = agent.plan_store.load("reject-plan")
        self._record(
            "reject_prevents_execution",
            "Reject prevents execution",
            bool(response) and response.status == "rejected" and persisted.metadata.get("status") == "rejected" and not calls,
            f"calls={len(calls)}; plan_status={persisted.metadata.get('status')}",
            hard=True,
        )

    def _run_defer_flow(self, root: Path) -> None:
        calls: list[dict[str, Any]] = []
        agent = self._blocking_agent(root / "defer", "agent.defer_target", calls)
        waiting = agent.executor.execute(self._plan("defer-plan", "agent.defer_target"))
        approval_id = waiting.approval_ids[0] if waiting.approval_ids else ""
        response = agent.defer_approval(approval_id, "2099-01-01T00:00:00Z") if approval_id else None
        approval = agent.approval_bridge.queue.get(approval_id) if approval_id else {}
        self._record(
            "defer_holds_plan",
            "Deferred approval keeps plan paused",
            bool(response) and response.status == "waiting_for_approval" and approval.get("status") == "deferred" and not calls,
            f"calls={len(calls)}; approval_status={approval.get('status', 'missing')}",
            hard=True,
        )

    def _run_mandatory_policy_checks(self, root: Path) -> None:
        cases = (
            ("delete_requires_approval", "Delete requires approval", "documents.delete", "delete", ToolCapability.DELETE),
            ("send_requires_approval", "Send requires approval", "mail.send", "send", ToolCapability.SEND),
            (
                "external_write_requires_approval",
                "External write requires approval",
                "connector.update",
                "external_write",
                ToolCapability.EXTERNAL_WRITE,
            ),
        )
        for check_id, title, tool_name, category, capability in cases:
            calls: list[dict[str, Any]] = []
            agent = self._agent(
                root / check_id,
                ToolDefinition(
                    tool_name,
                    title,
                    category=category,
                    capabilities=(capability,),
                    risk_level=ToolRiskLevel.LOW,
                    requires_approval=False,
                    handler=lambda payload, target=calls: target.append(dict(payload)) or {"done": True},
                ),
            )
            result = agent.executor.execute(self._plan(f"{check_id}-plan", tool_name))
            self._record(
                check_id,
                title,
                result.status == "waiting_for_approval" and not calls,
                f"status={result.status}; calls={len(calls)}",
                hard=True,
            )

    def _run_redaction_check(self, root: Path) -> None:
        secret = "gate-secret-value-9f31"
        target = root / "redaction"
        schema = ToolInputSchema(
            properties={"target": {"type": "string"}, "api_token": {"type": "string", "sensitive": True}},
            required=("target", "api_token"),
        )
        agent = self._agent(
            target,
            ToolDefinition(
                "connector.secure_write",
                "Secure connector write",
                category="connector_write",
                capabilities=(ToolCapability.CONNECTOR_WRITE,),
                input_schema=schema,
                handler=lambda payload: {"done": True},
            ),
        )
        result = agent.executor.execute(
            self._plan("redaction-plan", "connector.secure_write", {"target": "remote", "api_token": secret})
        )
        approval_id = result.approval_ids[0] if result.approval_ids else ""
        approval = agent.approval_bridge.queue.get(approval_id) if approval_id else {}
        persisted = "\n".join(path.read_text(encoding="utf-8") for path in target.rglob("*.json*") if path.is_file())
        detail = ApprovalInboxViewModel(target).detail(approval_id) if approval_id else {}
        rendered_detail = json.dumps(detail, ensure_ascii=False)
        redacted = approval.get("payload", {}).get("api_token") == "***" and secret not in persisted and secret not in rendered_detail
        self._record(
            "sensitive_payload_redacted",
            "Sensitive payload is redacted everywhere persisted or displayed",
            redacted,
            f"queue_redacted={approval.get('payload', {}).get('api_token') == '***'}; secret_found={secret in persisted or secret in rendered_detail}",
            hard=True,
        )

    def _run_restart_check(self, root: Path) -> None:
        target = root / "restart"
        calls: list[dict[str, Any]] = []
        agent = self._blocking_agent(target, "agent.restart_pending", calls)
        waiting = agent.executor.execute(self._plan("restart-plan", "agent.restart_pending"))
        approval_id = waiting.approval_ids[0] if waiting.approval_ids else ""
        reloaded_approval = NativeApprovalQueue(target).get(approval_id) if approval_id else None
        reloaded_plan = AgentPlanStore(target, registry=agent.registry).load("restart-plan")
        reloaded_view = ApprovalInboxViewModel(target).load(TAB_APPROVALS)
        visible = {item["item_id"] for item in reloaded_view.get("items", [])}
        retained = (
            bool(reloaded_approval)
            and reloaded_approval.get("status") == "pending"
            and reloaded_plan.metadata.get("status") == "waiting_for_approval"
            and approval_id in visible
        )
        self._record(
            "restart_retains_pending",
            "Restart retains pending approval and plan",
            retained,
            f"approval_present={bool(reloaded_approval)}; view_visible={approval_id in visible}",
            hard=True,
        )

    def _run_corrupt_queue_check(self, root: Path) -> None:
        target = root / "corrupt"
        path = approval_path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not-valid-json\n", encoding="utf-8")
        state = ApprovalInboxViewModel(target).load()
        controlled = state.get("ok") is False and state.get("status") == "error" and bool(state.get("error"))
        self._record(
            "corrupt_queue_controlled",
            "Corrupt queue produces a controlled error",
            controlled,
            f"view_status={state.get('status')}; has_error={bool(state.get('error'))}",
        )

    def _run_parallel_decision_check(self, root: Path) -> None:
        queue = NativeApprovalQueue(root / "parallel")
        approval = queue.create(
            command="agent.parallel_target",
            intent="gate:parallel",
            text="Concurrent decision check",
            plan_id="parallel-plan",
            step_id="parallel-step",
            tool_name="agent.parallel_target",
        )
        service = AgentApprovalService(queue=queue)
        original_read = queue._read_all  # noqa: SLF001 - deterministic race probe
        read_barrier = Barrier(2)

        def synchronized_read() -> list[dict[str, Any]]:
            rows = original_read()
            read_barrier.wait(timeout=5)
            return rows

        queue._read_all = synchronized_read  # type: ignore[method-assign]  # noqa: SLF001

        def decide(action: str) -> str:
            try:
                if action == "approve":
                    service.approve(approval["approval_id"], "parallel-approver")
                else:
                    service.reject(approval["approval_id"], "parallel-rejector")
                return f"{action}:accepted"
            except (ValueError, RuntimeError) as exc:
                return f"{action}:conflict:{type(exc).__name__}"

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = sorted(pool.map(decide, ("approve", "reject")))
        finally:
            queue._read_all = original_read  # type: ignore[method-assign]  # noqa: SLF001
        accepted = [outcome for outcome in outcomes if outcome.endswith(":accepted")]
        conflicts = [outcome for outcome in outcomes if ":conflict:" in outcome]
        self._record(
            "parallel_decision_conflict_safe",
            "Parallel decisions are conflict-safe",
            len(accepted) == 1 and len(conflicts) == 1,
            f"accepted={len(accepted)}; conflicts={len(conflicts)}; outcomes={','.join(outcomes)}",
        )

    @staticmethod
    def _agent(root: Path, definition: ToolDefinition) -> AgentCore:
        registry = ToolRegistry()
        registry.register(definition)
        bridge = AgentApprovalBridge(root)
        return AgentCore(registry=registry, approval_bridge=bridge, project_root=root)

    def _blocking_agent(self, root: Path, tool_name: str, calls: list[dict[str, Any]]) -> AgentCore:
        return self._agent(
            root,
            ToolDefinition(
                tool_name,
                "Approval-gated operation",
                risk_level=ToolRiskLevel.HIGH,
                requires_approval=True,
                handler=lambda payload: calls.append(dict(payload)) or {"done": True},
            ),
        )

    @staticmethod
    def _plan(plan_id: str, tool_name: str, payload: dict[str, Any] | None = None) -> TaskPlan:
        return TaskPlan(
            plan_id=plan_id,
            intent=f"gate:{tool_name}",
            steps=[TaskStep(step_id=f"{plan_id}-step", name=tool_name, tool_name=tool_name, payload=payload or {})],
        )

    def _record(
        self,
        check_id: str,
        title: str,
        passed: bool,
        detail: str,
        *,
        hard: bool = False,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self._checks.append(GateCheck(check_id, title, bool(passed), detail, hard, evidence or {}))


def run_review_approval_gate(project_root: str | Path = ".") -> dict[str, Any]:
    """Public launcher/test entrypoint."""

    try:
        return ReviewApprovalGate(project_root).run()
    except Exception as exc:  # noqa: BLE001 - gate must always return a controlled verdict
        return {
            "schema": "secondbrain.review_approval_gate.v1",
            "status": BLOCKED,
            "ok": False,
            "project_root": str(Path(project_root).resolve()),
            "summary": {"total": 0, "passed": 0, "conditional": 0, "blocked": 1},
            "checks": [],
            "blockers": [f"gate_internal_error:{type(exc).__name__}:{exc}"],
            "warnings": [],
        }
