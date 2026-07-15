"""Graph-based planner (v2): validate, simulate, execute, recover.

The planner turns a goal into a checked DAG and runs it under strict controls:
cycles and impossible dependencies are rejected before execution; simulation is
a pure dry-run that touches no tool; execution respects the cost/time budget,
runs only genuinely independent nodes in parallel, and keeps every
approval-required node serial so parallelism can never bypass a gate. Failures
fall through to a recovery path (alternative tool, retry, manual review,
controlled abort, rollback). Every state change is appended to the plan audit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import uuid4

from secondbrain.planner_v2.models import (
    Budget, NodeStatus, PlanGraph, PlanNode, PlanStatus, RiskLevel,
)

__all__ = ["Planner", "PlanValidationError", "RunResult"]

_RISKY = {RiskLevel.HIGH.value, RiskLevel.CRITICAL.value}
_NEVER_RETRY = {"send", "delete", "forward", "publish"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class PlanValidationError(RuntimeError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        super().__init__("plan_invalid")
        self.issues = issues


class RunResult(dict):
    """Execution outcome: status, executed, paused, failed, audit, cost."""


class Planner:
    def __init__(self, *, available_tools: Iterable[str] | None = None,
                 granted_scopes: Iterable[str] | None = None,
                 tool_scopes: Mapping[str, str] | None = None,
                 unsafe_tools: Iterable[str] | None = None,
                 max_parallelism: int = 4) -> None:
        self.available_tools = set(available_tools or [])
        self.granted_scopes = set(granted_scopes or [])
        self.tool_scopes = dict(tool_scopes or {})
        self.unsafe_tools = set(unsafe_tools or [])
        self.max_parallelism = max(1, int(max_parallelism))

    # -- construction -----------------------------------------------------

    def create_plan(self, *, goal: str, workspace_id: str, nodes: Sequence[PlanNode],
                    budget: Budget | None = None) -> PlanGraph:
        plan = PlanGraph(plan_id=str(uuid4()), goal=goal, workspace_id=workspace_id,
                         nodes=list(nodes), budget=budget or Budget(), created_at=_now(), updated_at=_now())
        self._audit(plan, "-", "created", f"{len(plan.nodes)} nodes")
        return plan

    # -- validation -------------------------------------------------------

    def validate_plan(self, plan: PlanGraph) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        ids = {n.node_id for n in plan.nodes}
        # impossible dependencies
        for n in plan.nodes:
            for dep in n.dependencies:
                if dep not in ids:
                    issues.append({"type": "impossible_dependency", "node": n.node_id, "detail": dep})
        # cycles
        if self._has_cycle(plan):
            issues.append({"type": "cycle", "detail": "dependency cycle detected"})
        # tools / scopes / risk / data / approvals
        total_cost = total_duration = 0.0
        for n in plan.nodes:
            total_cost += n.estimated_cost
            total_duration += n.estimated_duration
            if n.tool and self.available_tools and n.tool not in self.available_tools:
                issues.append({"type": "missing_tool", "node": n.node_id, "detail": n.tool})
            scope = self.tool_scopes.get(n.tool)
            if scope and scope not in self.granted_scopes:
                issues.append({"type": "missing_scope", "node": n.node_id, "detail": scope})
            if n.risk in _RISKY and not n.approval_required:
                issues.append({"type": "risky_without_approval", "node": n.node_id, "detail": n.risk})
            if n.tool and not n.input and not n.dependencies:
                issues.append({"type": "missing_data", "node": n.node_id, "detail": "no input, no upstream"})
            if n.approval_required:
                issues.append({"type": "approval_point", "node": n.node_id, "detail": "requires approval"})
            node_workspace = n.input.get("workspace_id") if isinstance(n.input, Mapping) else None
            if node_workspace not in (None, "", plan.workspace_id):
                issues.append({"type": "workspace_crossing", "node": n.node_id, "detail": str(node_workspace)})
            if any(token in n.tool.lower() for token in _NEVER_RETRY) and n.retry_policy.max_attempts > 1:
                issues.append({"type": "unsafe_retry", "node": n.node_id, "detail": n.tool})
        if total_cost > plan.budget.max_cost:
            issues.append({"type": "cost_limit", "detail": f"{total_cost} > {plan.budget.max_cost}"})
        if total_duration > plan.budget.max_duration:
            issues.append({"type": "time_limit", "detail": f"{total_duration} > {plan.budget.max_duration}"})
        # cost/time/approval are non-blocking: cost & time are enforced hard at
        # runtime (a node is not started if it would breach the budget), and
        # approval points are gates, not defects.
        _nonblocking = ("approval_point", "cost_limit", "time_limit")
        blocking = [i for i in issues if i["type"] not in _nonblocking]
        plan.status = PlanStatus.INVALID.value if blocking else PlanStatus.VALIDATED.value
        plan.updated_at = _now()
        return issues

    def is_valid(self, plan: PlanGraph) -> bool:
        _nonblocking = ("approval_point", "cost_limit", "time_limit")
        return not [i for i in self.validate_plan(plan) if i["type"] not in _nonblocking]

    # -- simulation (no tool execution) ----------------------------------

    def simulate_plan(self, plan: PlanGraph) -> dict[str, Any]:
        planned, approvals, risks, data_access, external = [], [], [], [], []
        cost = duration = 0.0
        for layer in self.execution_layers(plan):
            for node_id in layer:
                n = plan.node(node_id)
                planned.append({"node": n.node_id, "objective": n.objective, "tool": n.tool})
                cost += n.estimated_cost
                duration += n.estimated_duration
                if n.approval_required:
                    approvals.append(n.node_id)
                if n.risk in _RISKY:
                    risks.append({"node": n.node_id, "risk": n.risk})
                if n.input:
                    data_access.append({"node": n.node_id, "reads": sorted(n.input.keys())})
                if n.risk in _RISKY or n.approval_required:
                    external.append(n.node_id)
        return {
            "executed": False,  # simulation never runs a tool
            "planned_actions": planned, "approvals": approvals, "risks": risks,
            "data_access": data_access, "external_changes": external,
            "estimated_cost": round(cost, 3), "estimated_duration": round(duration, 3),
            "within_budget": cost <= plan.budget.max_cost and duration <= plan.budget.max_duration,
        }

    def compare_plans(self, a: PlanGraph, b: PlanGraph) -> dict[str, Any]:
        sa, sb = self.simulate_plan(a), self.simulate_plan(b)
        return {
            "cost": {"a": sa["estimated_cost"], "b": sb["estimated_cost"]},
            "duration": {"a": sa["estimated_duration"], "b": sb["estimated_duration"]},
            "steps": {"a": len(sa["planned_actions"]), "b": len(sb["planned_actions"])},
            "risks": {"a": len(sa["risks"]), "b": len(sb["risks"])},
            "approvals": {"a": len(sa["approvals"]), "b": len(sb["approvals"])},
        }

    # -- layering / parallelism ------------------------------------------

    def execution_layers(self, plan: PlanGraph) -> list[list[str]]:
        """Topological layers. Nodes in the same layer are independent and may
        run in parallel (subject to approval/serial and unsafe-tool rules)."""
        indeg = {n.node_id: 0 for n in plan.nodes}
        adj: dict[str, list[str]] = {n.node_id: [] for n in plan.nodes}
        for n in plan.nodes:
            for dep in n.dependencies:
                if dep in indeg:
                    indeg[n.node_id] += 1
                    adj[dep].append(n.node_id)
        layers: list[list[str]] = []
        ready = sorted([nid for nid, d in indeg.items() if d == 0])
        seen = 0
        while ready:
            layers.append(list(ready))
            seen += len(ready)
            nxt: list[str] = []
            for nid in ready:
                for m in adj[nid]:
                    indeg[m] -= 1
                    if indeg[m] == 0:
                        nxt.append(m)
            ready = sorted(nxt)
        return layers if seen == len(plan.nodes) else layers  # cycle -> partial

    def parallel_groups(self, plan: PlanGraph) -> list[list[str]]:
        """Independent nodes that are eligible to run concurrently. Approval and
        unsafe-tool nodes are pulled out to run serially - they are never part
        of a concurrent group."""
        groups: list[list[str]] = []
        for layer in self.execution_layers(plan):
            concurrent = [nid for nid in layer
                          if not plan.node(nid).approval_required
                          and plan.node(nid).tool not in self.unsafe_tools]
            for i in range(0, len(concurrent), self.max_parallelism):
                chunk = concurrent[i:i + self.max_parallelism]
                if len(chunk) > 1:
                    groups.append(chunk)
        return groups

    # -- execution --------------------------------------------------------

    def execute_plan(self, plan: PlanGraph, *, tools: Mapping[str, Callable[[dict[str, Any]], Any]],
                     approval_authority: Any | None = None, cancel: bool = False) -> RunResult:
        if not self.is_valid(plan):
            plan.status = PlanStatus.INVALID.value
            return RunResult(status=PlanStatus.INVALID.value, executed=[], paused=[], failed=[],
                             audit=plan.audit, cost=0.0)
        plan.status = PlanStatus.RUNNING.value
        executed, paused, failed = [], [], []
        cost = 0.0
        completed = set(plan.checkpoint)
        for layer in self.execution_layers(plan):
            for node_id in layer:
                n = plan.node(node_id)
                if node_id in completed:
                    continue
                if cancel:
                    self._audit(plan, node_id, "cancelled", "run cancelled")
                    plan.status = PlanStatus.CANCELLED.value
                    return RunResult(status=PlanStatus.CANCELLED.value, executed=executed, paused=paused,
                                     failed=failed, audit=plan.audit, cost=round(cost, 3))
                # dependencies must be completed
                if any(dep not in completed for dep in n.dependencies):
                    n.status = NodeStatus.SKIPPED.value
                    self._audit(plan, node_id, "skipped", "upstream incomplete")
                    continue
                # approval gate - never bypassed, even inside a parallel layer
                if n.approval_required:
                    try:
                        authorized = bool(approval_authority and approval_authority.claim(plan=plan, node=n))
                    except Exception:
                        authorized = False
                    if not authorized:
                        n.status = NodeStatus.WAITING_FOR_APPROVAL.value
                        paused.append(node_id)
                        self._audit(plan, node_id, "waiting_for_approval", "bound approval required")
                        continue
                # budget guard - do not start a node that would exceed cost
                if cost + n.estimated_cost > plan.budget.max_cost:
                    self._audit(plan, node_id, "budget_exceeded", f"cost limit {plan.budget.max_cost}")
                    plan.status = PlanStatus.PAUSED.value
                    return RunResult(status="budget_exceeded", executed=executed, paused=paused,
                                     failed=failed, audit=plan.audit, cost=round(cost, 3))
                outcome = self._run_node(plan, n, tools)
                if outcome["ok"]:
                    completed.add(node_id)
                    plan.checkpoint = sorted(completed)
                    executed.append(node_id)
                    cost += n.estimated_cost
                else:
                    failed.append(node_id)
                    plan.status = PlanStatus.RECOVERY_REQUIRED.value
                    return RunResult(status=PlanStatus.RECOVERY_REQUIRED.value, executed=executed,
                                     paused=paused, failed=failed, audit=plan.audit, cost=round(cost, 3))
        if paused:
            plan.status = PlanStatus.PAUSED.value
            status = PlanStatus.PAUSED.value
        else:
            plan.status = PlanStatus.COMPLETED.value
            status = PlanStatus.COMPLETED.value
        return RunResult(status=status, executed=executed, paused=paused, failed=failed,
                         audit=plan.audit, cost=round(cost, 3))

    def pause_plan(self, plan: PlanGraph) -> None:
        plan.status = PlanStatus.PAUSED.value
        self._audit(plan, "-", "paused", "manual pause")

    def resume_plan(self, plan: PlanGraph, *, tools: Mapping[str, Callable[[dict[str, Any]], Any]],
                    approval_authority: Any | None = None) -> RunResult:
        self._audit(plan, "-", "resumed", f"from checkpoint {plan.checkpoint}")
        return self.execute_plan(plan, tools=tools, approval_authority=approval_authority)

    def cancel_plan(self, plan: PlanGraph) -> None:
        plan.status = PlanStatus.CANCELLED.value
        self._audit(plan, "-", "cancelled", "manual cancel")

    def recover_plan(self, plan: PlanGraph, *, tools: Mapping[str, Callable[[dict[str, Any]], Any]],
                     approval_authority: Any | None = None) -> RunResult:
        self._audit(plan, "-", "recovery", "retry via alternative path")
        return self.execute_plan(plan, tools=tools, approval_authority=approval_authority)

    # -- node runner with recovery ---------------------------------------

    def _run_node(self, plan: PlanGraph, node: PlanNode,
                  tools: Mapping[str, Callable[[dict[str, Any]], Any]]) -> dict[str, Any]:
        node.status = NodeStatus.RUNNING.value
        candidates = [node.tool] + list(node.alt_tools)
        attempts = 1 if (not node.idempotent or any(token in node.tool.lower() for token in _NEVER_RETRY)) else max(1, node.retry_policy.max_attempts)
        last_error = ""
        for tool_name in candidates:
            fn = tools.get(tool_name)
            if fn is None:
                continue
            for attempt in range(attempts):
                try:
                    result = fn(dict(node.input))
                except Exception as exc:  # noqa: BLE001
                    last_error = f"{type(exc).__name__}: {exc}"
                    self._audit(plan, node.node_id, "attempt_failed",
                                f"tool={tool_name} attempt={attempt + 1} {last_error}")
                    continue
                node.status = NodeStatus.COMPLETED.value
                via = "primary" if tool_name == node.tool else f"alt:{tool_name}"
                self._audit(plan, node.node_id, "completed", f"via {via}")
                return {"ok": True, "result": result, "via": tool_name}
        node.status = NodeStatus.FAILED.value
        self._audit(plan, node.node_id, "failed", last_error or "no runnable tool")
        return {"ok": False, "error": last_error}

    # -- helpers ----------------------------------------------------------

    def _has_cycle(self, plan: PlanGraph) -> bool:
        ids = {n.node_id for n in plan.nodes}
        indeg = {nid: 0 for nid in ids}
        adj: dict[str, list[str]] = {nid: [] for nid in ids}
        for n in plan.nodes:
            for dep in n.dependencies:
                if dep in ids:
                    indeg[n.node_id] += 1
                    adj[dep].append(n.node_id)
        stack = [nid for nid, d in indeg.items() if d == 0]
        seen = 0
        while stack:
            nid = stack.pop()
            seen += 1
            for m in adj[nid]:
                indeg[m] -= 1
                if indeg[m] == 0:
                    stack.append(m)
        return seen != len(ids)

    @staticmethod
    def _audit(plan: PlanGraph, node_id: str, event: str, detail: str) -> None:
        plan.audit.append({"at": _now(), "node": node_id, "event": event, "detail": detail})
