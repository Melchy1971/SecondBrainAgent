"""v30.69 Multi-Agent Coordination - Coordinator.

Orchestrates the existing specialist agents through a shared workspace and a
communication bus. Task delegation routes each task to the specialist whose
capabilities cover its kind. ``solve`` runs the collaboration pipeline
plan -> critique -> review -> (execute).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agents import SpecialistAgent, default_agents
from .bus import CommunicationBus
from .models import (
    KIND_CRITIQUE,
    KIND_EXECUTE,
    KIND_PLAN,
    KIND_REVIEW,
    AgentResult,
    AgentTask,
)
from .shared import SharedContext, SharedGoals, SharedMemory


@dataclass
class CoordinationWorkspace:
    project_root: Path
    context: SharedContext
    memory: SharedMemory
    bus: CommunicationBus
    goals: SharedGoals | None = None


class Coordinator:
    role = "coordinator"

    def __init__(
        self,
        project_root: str | Path,
        *,
        agents: list[SpecialistAgent] | None = None,
        memory_store: Any | None = None,
        bus: CommunicationBus | None = None,
        with_goals: bool = True,
    ):
        self.project_root = Path(project_root).resolve()
        self.bus = bus or CommunicationBus(self.project_root)
        goals = None
        if with_goals:
            try:
                goals = SharedGoals(project_root=self.project_root)
            except Exception:
                goals = None
        self.workspace = CoordinationWorkspace(
            project_root=self.project_root,
            context=SharedContext(),
            memory=SharedMemory(memory_store, project_root=self.project_root),
            bus=self.bus,
            goals=goals,
        )
        self.agents: list[SpecialistAgent] = list(agents) if agents is not None else default_agents()

    # -- registry / delegation --------------------------------------------
    def register(self, agent: SpecialistAgent) -> None:
        self.agents.append(agent)

    def agent_for(self, kind: str) -> SpecialistAgent | None:
        return next((a for a in self.agents if a.can_handle(kind)), None)

    def capabilities(self) -> dict[str, str]:
        return {kind: a.role for a in self.agents for kind in a.capabilities}

    def delegate(self, task: AgentTask) -> AgentResult:
        agent = self.agent_for(task.kind)
        self.bus.publish(f"task:{task.kind}", self.role, task.to_dict())
        if agent is None:
            result = AgentResult.failure(task.id, self.role, f"no_agent_for_kind:{task.kind}")
        else:
            try:
                result = agent.handle(task, self.workspace)
            except Exception as exc:  # noqa: BLE001 - one agent must not crash the run
                result = AgentResult.failure(task.id, getattr(agent, "role", "?"), str(exc))
        self.bus.publish("result", result.agent, result.to_dict())
        return result

    def delegate_kind(self, kind: str, payload: dict | None = None) -> AgentResult:
        return self.delegate(AgentTask.create(kind, payload))

    # -- collaboration pipeline -------------------------------------------
    def solve(self, goal: str, *, execute: bool = True) -> dict[str, Any]:
        plan_res = self.delegate_kind(KIND_PLAN, {"goal": goal})
        if not plan_res.ok:
            return {"ok": False, "stage": "plan", "error": plan_res.error}
        plan = plan_res.output

        critique = self.delegate_kind(KIND_CRITIQUE, {"plan": plan})
        review = self.delegate_kind(KIND_REVIEW, {"plan": plan})

        execution = None
        approved = bool(review.ok and review.output.get("approved"))
        severe = bool(critique.ok and critique.output.get("severity") == "high")
        if execute and approved and not severe:
            steps = [{"id": s["id"], "name": s.get("title", s["id"])} for s in plan.get("steps", [])]
            execution = self.delegate_kind(KIND_EXECUTE, {"objective": goal, "steps": steps})

        summary = {
            "ok": True,
            "goal": goal,
            "plan": plan,
            "critique": critique.output if critique.ok else {"error": critique.error},
            "review": review.output if review.ok else {"error": review.error},
            "executed": execution is not None,
            "execution": execution.output if (execution and execution.ok) else None,
            "approved": approved,
            "messages": len(self.bus.log),
        }
        self.workspace.context.set("solution", summary, by=self.role)
        return summary

    # -- shared surfaces ---------------------------------------------------
    def context(self) -> SharedContext:
        return self.workspace.context

    def memory(self) -> SharedMemory:
        return self.workspace.memory

    def goals(self) -> SharedGoals | None:
        return self.workspace.goals
