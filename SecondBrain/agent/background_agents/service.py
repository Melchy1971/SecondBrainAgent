"""v30.63 Background Agents - service facade for the launcher CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import AgentFailurePolicy, AgentSchedule, AgentType
from .supervisor import AgentSupervisor


class BackgroundAgentService:
    def __init__(self, project_root: str | Path, *, supervisor: AgentSupervisor | None = None, **overrides: Any):
        self.project_root = Path(project_root).resolve()
        self.supervisor = supervisor or AgentSupervisor.for_project(self.project_root, **overrides)

    def register(self, name: str, agent_type: str, *, interval_seconds: int = 0,
                 max_consecutive_failures: int = 3, action: str = "pause",
                 config: dict | None = None) -> dict[str, Any]:
        agent = self.supervisor.register(
            name, agent_type,
            schedule=AgentSchedule(interval_seconds=interval_seconds),
            failure_policy=AgentFailurePolicy(max_consecutive_failures=max_consecutive_failures, action=action),
            config=config or {},
        )
        return {"ok": True, "agent": agent.to_dict()}

    def list(self) -> dict[str, Any]:
        agents = self.supervisor.list()
        return {"ok": True, "count": len(agents), "agents": agents}

    def start(self, agent_id: str) -> dict[str, Any]:
        return {"ok": True, "agent": self.supervisor.start(agent_id).to_dict()}

    def stop(self, agent_id: str) -> dict[str, Any]:
        return {"ok": True, "agent": self.supervisor.stop(agent_id).to_dict()}

    def pause(self, agent_id: str) -> dict[str, Any]:
        return {"ok": True, "agent": self.supervisor.pause(agent_id).to_dict()}

    def status(self, agent_id: str) -> dict[str, Any]:
        return {"ok": True, **self.supervisor.status(agent_id)}

    def run(self, agent_id: str, *, force: bool = False) -> dict[str, Any]:
        return {"ok": True, "run": self.supervisor.run_agent(agent_id, force=force).to_dict()}

    def run_due(self) -> dict[str, Any]:
        runs = self.supervisor.run_due()
        return {"ok": True, "ran": len(runs), "runs": [r.to_dict() for r in runs]}

    def runs(self, agent_id: str | None = None, *, limit: int = 50) -> dict[str, Any]:
        rows = self.supervisor.runs(agent_id, limit=limit)
        return {"ok": True, "count": len(rows), "runs": rows}

    def heartbeat(self, agent_id: str) -> dict[str, Any]:
        return {"ok": True, "heartbeat": self.supervisor.heartbeat(agent_id).to_dict()}

    @staticmethod
    def agent_types() -> list[str]:
        return [t.value for t in AgentType]
