"""v30.69 Multi-Agent Coordination - specialist agents.

Each specialist is a thin adapter over an EXISTING subsystem - it adds no new
engine, it gives the coordinator a uniform ``handle(task, workspace)`` surface.

    PlannerAgent  -> AgentPlanService (v30.59)
    ExecutorAgent -> WorkflowExecutor (v30.62)
    CriticAgent   -> ReasoningSession (v30.68)
    ReviewerAgent -> deterministic plan checks
    MemoryAgent   -> SharedMemory (memory store + MemoryInjector)
    SearchAgent   -> SharedMemory.recall (memory injection)
    ImportAgent   -> JobQueueService snapshot (v30.44)
"""

from __future__ import annotations

from typing import Any

from .models import (
    KIND_CRITIQUE,
    KIND_EXECUTE,
    KIND_IMPORT_CHECK,
    KIND_MEMORY_RECALL,
    KIND_MEMORY_STORE,
    KIND_PLAN,
    KIND_REVIEW,
    KIND_SEARCH,
    AgentResult,
    AgentTask,
)


class SpecialistAgent:
    role: str = "specialist"
    capabilities: frozenset[str] = frozenset()

    def can_handle(self, kind: str) -> bool:
        return kind in self.capabilities

    def handle(self, task: AgentTask, workspace) -> AgentResult:  # pragma: no cover - abstract
        raise NotImplementedError


class PlannerAgent(SpecialistAgent):
    role = "planner"
    capabilities = frozenset({KIND_PLAN})

    def __init__(self, planner: Any | None = None):
        self._planner = planner

    def _svc(self, workspace):
        if self._planner is not None:
            return self._planner
        from secondbrain.agent.planner import AgentPlanService
        return AgentPlanService(workspace.project_root)

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        goal = task.payload.get("goal", "")
        if not goal:
            return AgentResult.failure(task.id, self.role, "goal_required")
        plan = self._svc(workspace).create(goal, workspace_id=task.payload.get("workspace_id"))
        d = plan.to_dict()
        workspace.context.set("plan", d, by=self.role)
        return AgentResult.success(task.id, self.role, d)


class CriticAgent(SpecialistAgent):
    role = "critic"
    capabilities = frozenset({KIND_CRITIQUE})

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        from secondbrain.agent.reasoning import ReasoningSession
        from secondbrain.agent.reasoning.models import REFUTE, SUPPORT, Evidence

        plan = task.payload.get("plan") or workspace.context.get("plan") or {}
        steps = plan.get("steps", [])
        risks: list[str] = []
        session = ReasoningSession("Ist der Plan sicher ausführbar?")
        hyp = session.hypothesize("Der Plan ist sicher ausführbar")
        for step in steps:
            if step.get("risk_level") in {"high", "critical"}:
                risks.append(f"high_risk_step:{step.get('id')}")
                ev = session.add_evidence(Evidence.create(
                    f"Schritt {step.get('id')} hat Risiko {step.get('risk_level')}",
                    source="critic", confidence=0.8))
                session.link_evidence(hyp.id, ev.id, REFUTE)
            elif step.get("requires_approval"):
                risks.append(f"requires_approval:{step.get('id')}")
            if not step.get("expected_output"):
                risks.append(f"missing_expected_output:{step.get('id')}")
        if not risks:
            ev = session.add_evidence(Evidence.create("Keine riskanten Schritte", source="critic",
                                                      confidence=0.7))
            session.link_evidence(hyp.id, ev.id, SUPPORT)
        tested = session.test_hypothesis(hyp.id)
        severity = "high" if any(r.startswith("high_risk_step") for r in risks) else (
            "medium" if risks else "low")
        output = {"status": tested.status, "risks": risks, "severity": severity,
                  "support_score": tested.support_score}
        workspace.context.set("critique", output, by=self.role)
        return AgentResult.success(task.id, self.role, output)


class ReviewerAgent(SpecialistAgent):
    role = "reviewer"
    capabilities = frozenset({KIND_REVIEW})

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        plan = task.payload.get("plan") or workspace.context.get("plan") or {}
        steps = plan.get("steps", [])
        notes: list[str] = []
        if not steps:
            notes.append("plan_has_no_steps")
        for step in steps:
            if not step.get("expected_output"):
                notes.append(f"step_missing_expected_output:{step.get('id')}")
        status = str(plan.get("status", ""))
        if status and status not in {"validated", "completed", "pending"}:
            notes.append(f"unexpected_plan_status:{status}")
        approved = not notes
        output = {"approved": approved, "notes": notes, "reviewed_steps": len(steps)}
        workspace.context.set("review", output, by=self.role)
        return AgentResult.success(task.id, self.role, output)


class ExecutorAgent(SpecialistAgent):
    role = "executor"
    capabilities = frozenset({KIND_EXECUTE})

    def __init__(self, tool_runner=None):
        self._tool_runner = tool_runner or (lambda step, approved: "ok")

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        from secondbrain.agent.workflow import WorkflowExecutor
        from secondbrain.agent.workflow_models import WorkflowStep

        objective = task.payload.get("objective", "coordination")
        raw_steps = task.payload.get("steps")
        if raw_steps is None:
            plan = workspace.context.get("plan") or {}
            raw_steps = [{"id": s["id"], "name": s.get("title", s["id"])}
                         for s in plan.get("steps", [])]
        if not raw_steps:
            return AgentResult.failure(task.id, self.role, "no_steps_to_execute")
        steps = [WorkflowStep(id=str(s["id"]), name=s.get("name", str(s["id"])),
                              tool_name=s.get("tool_name")) for s in raw_steps]
        ex = WorkflowExecutor(workspace.project_root, tool_runner=self._tool_runner)
        cp = ex.create(objective, steps)
        cp = ex.run(cp.workflow_id)
        output = {"workflow_id": cp.workflow_id, "state": cp.state.value}
        workspace.context.set("execution", output, by=self.role)
        return AgentResult.success(task.id, self.role, output)


class MemoryAgent(SpecialistAgent):
    role = "memory"
    capabilities = frozenset({KIND_MEMORY_STORE, KIND_MEMORY_RECALL})

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        if task.kind == KIND_MEMORY_STORE:
            text = task.payload.get("text", "")
            if not text:
                return AgentResult.failure(task.id, self.role, "text_required")
            workspace.memory.remember(text, source=task.payload.get("source", "agent"))
            return AgentResult.success(task.id, self.role, {"stored": True})
        query = task.payload.get("query", "")
        hits = workspace.memory.recall(query, limit=task.payload.get("limit", 10))
        return AgentResult.success(task.id, self.role, {"hits": hits, "count": len(hits)})


class SearchAgent(SpecialistAgent):
    role = "search"
    capabilities = frozenset({KIND_SEARCH})

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        query = task.payload.get("query", "")
        if not query:
            return AgentResult.failure(task.id, self.role, "query_required")
        hits = workspace.memory.recall(query, limit=task.payload.get("limit", 10),
                                       privacy_mode=task.payload.get("privacy_mode", False))
        return AgentResult.success(task.id, self.role, {"results": hits, "count": len(hits)})


class ImportAgent(SpecialistAgent):
    role = "import"
    capabilities = frozenset({KIND_IMPORT_CHECK})

    def __init__(self, jobs: Any | None = None):
        self._jobs = jobs

    def handle(self, task: AgentTask, workspace) -> AgentResult:
        jobs = self._jobs
        if jobs is None:
            from secondbrain.native.job_queue_center.service import JobQueueService
            jobs = JobQueueService(root=workspace.project_root)
        snap = jobs.snapshot()
        imports = [j for j in snap.get("jobs", []) if j.get("kind") == "import"]
        blocked = [j for j in imports if j.get("status") in {"blocked", "failed", "dead_letter"}]
        return AgentResult.success(task.id, self.role, {
            "import_jobs": len(imports), "blocked_or_failed": len(blocked),
            "healthy": len(blocked) == 0})


def default_agents() -> list[SpecialistAgent]:
    return [PlannerAgent(), CriticAgent(), ReviewerAgent(), ExecutorAgent(),
            MemoryAgent(), SearchAgent(), ImportAgent()]
