
from __future__ import annotations
from pathlib import Path
from typing import Any
from .common import JsonStore, now_iso
from .registry import AgentRegistry
from .context_store import SharedContextStore
from .messaging import AgentMessageBus
from .supervisor import SupervisorAgent
from .planner import PlannerAgent
from .researcher import ResearchAgent
from .executor import ExecutorAgent
from .reviewer import ReviewerAgent
from .memory_curator import MemoryCuratorAgent
from .consensus import ConsensusEngine
from .recovery import SwarmRecovery

class SwarmKernel:
    def __init__(self, runtime_dir: str | Path, event_bus: Any | None = None, tool_registry: Any | None = None, graph_engine: Any | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.base = self.runtime_dir / "swarm_v124"
        self.base.mkdir(parents=True, exist_ok=True)
        self.event_bus = event_bus
        self.tool_registry = tool_registry
        self.graph_engine = graph_engine
        self.registry = AgentRegistry(runtime_dir)
        self.context = SharedContextStore(runtime_dir)
        self.messages = AgentMessageBus(runtime_dir, event_bus)
        self.consensus = ConsensusEngine(runtime_dir)
        self.recovery = SwarmRecovery(runtime_dir)
        self.tasks = JsonStore(self.base / "tasks.json", [])
        self.plans = JsonStore(self.base / "plans.json", [])
        self.results = JsonStore(self.base / "results.json", [])
        self.history = JsonStore(self.base / "history.json", [])
        self.supervisor = SupervisorAgent()
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()
        self.memory_curator = MemoryCuratorAgent()

    def _save_task(self, task: dict[str, Any]) -> None:
        rows = self.tasks.read()
        replaced = False
        for i, row in enumerate(rows):
            if row.get("id") == task.get("id"):
                rows[i] = task
                replaced = True
                break
        if not replaced:
            rows.append(task)
        self.tasks.write(rows)

    def _get_task(self, task_id: str) -> dict[str, Any]:
        for task in self.tasks.read():
            if task.get("id") == task_id:
                return task
        raise KeyError(f"Unknown swarm task: {task_id}")

    def _event(self, topic: str, payload: dict[str, Any], task_id: str | None = None, risk_level: int = 1) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(topic, "swarm_v124", payload, risk_level=risk_level, correlation_id=task_id)

    def status(self) -> dict[str, Any]:
        tasks = self.tasks.read()
        return {
            "component": "swarm_kernel_v124",
            "healthy": True,
            "agents": self.registry.status(),
            "tasks": len(tasks),
            "running": sum(1 for t in tasks if t.get("status") == "running"),
            "completed": sum(1 for t in tasks if t.get("status") == "completed"),
            "failed": sum(1 for t in tasks if t.get("status") == "failed"),
            "messages": self.messages.status(),
            "context": self.context.status(),
        }

    def agents(self) -> list[dict[str, Any]]:
        return self.registry.list_agents()

    def run(self, objective: str, priority: str = "normal") -> dict[str, Any]:
        task = self.supervisor.create_task(objective, priority)
        task_id = task["id"]
        self._save_task(task)
        self._event("swarm.task.created", task, task_id)
        self.history.append({"task_id": task_id, "event": "created", "created_at": now_iso()})

        try:
            task["status"] = "running"; task["updated_at"] = now_iso(); self._save_task(task)
            analysis = self.supervisor.analyze(task)
            self.context.put(task_id, "analysis", analysis, "supervisor")
            self.messages.send(task_id, "supervisor", "planner", "analysis", analysis)

            plan = self.planner.decompose(objective, {"analysis": analysis})
            plan["task_id"] = task_id
            self.plans.append(plan)
            self.context.put(task_id, "plan", plan, "planner")
            self._event("swarm.plan.created", plan, task_id)

            research = self.researcher.research(objective, self.context.get_task(task_id), self.graph_engine)
            self.context.put(task_id, "research", research, "researcher")
            self.messages.send(task_id, "researcher", "executor", "research", research)
            self._event("swarm.research.completed", research, task_id)

            execution = self.executor.execute(objective, self.context.get_task(task_id), self.tool_registry)
            self.context.put(task_id, "execution", execution, "executor")
            self.messages.send(task_id, "executor", "reviewer", "execution", execution)
            self._event("swarm.execution.completed", execution, task_id)

            review = self.reviewer.review(objective, self.context.get_task(task_id))
            self.context.put(task_id, "review", review, "reviewer")
            self.messages.send(task_id, "reviewer", "memory_curator", "review", review)
            self._event("swarm.review.completed", review, task_id)

            memory = self.memory_curator.curate(objective, self.context.get_task(task_id) | {"task_id": task_id}, self.graph_engine)
            self.context.put(task_id, "memory", memory, "memory_curator")
            self._event("swarm.memory.updated", memory, task_id)

            consensus = self.consensus.evaluate(task_id, self.context.get_task(task_id))
            self.context.put(task_id, "consensus", consensus, "consensus")

            result = {
                "task_id": task_id,
                "objective": objective,
                "status": "completed" if consensus["decision"] == "accepted" else "needs_revision",
                "plan": plan,
                "research": research,
                "execution": execution,
                "review": review,
                "memory": memory,
                "consensus": consensus,
                "completed_at": now_iso(),
            }
            self.results.append(result)
            task["status"] = result["status"]; task["updated_at"] = now_iso(); self._save_task(task)
            self.history.append({"task_id": task_id, "event": result["status"], "created_at": now_iso()})
            return result
        except Exception as exc:
            task["status"] = "failed"; task["error"] = str(exc); task["updated_at"] = now_iso(); self._save_task(task)
            self._event("swarm.failed", {"task_id": task_id, "error": str(exc)}, task_id, risk_level=2)
            self.history.append({"task_id": task_id, "event": "failed", "error": str(exc), "created_at": now_iso()})
            raise

    def task(self, task_id: str) -> dict[str, Any]:
        return {
            "task": self._get_task(task_id),
            "context": self.context.get_task(task_id),
            "messages": self.messages.list(task_id),
            "consensus": self.consensus.list(task_id),
        }

    def history_rows(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.history.read()[-limit:]

    def consensus_rows(self, task_id: str | None = None) -> list[dict[str, Any]]:
        return self.consensus.list(task_id)

    def recover(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        row = self.recovery.recover(task)
        task["status"] = "recoverable"; task["updated_at"] = now_iso()
        self._save_task(task)
        return row

    def stop(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task.get("status") in {"completed", "failed"}:
            return {"task_id": task_id, "status": task.get("status"), "changed": False}
        task["status"] = "stopped"; task["updated_at"] = now_iso()
        self._save_task(task)
        return {"task_id": task_id, "status": "stopped", "changed": True}
