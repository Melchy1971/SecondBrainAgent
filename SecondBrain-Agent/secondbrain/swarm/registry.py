
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from .common import JsonStore, now_iso

@dataclass
class AgentDefinition:
    name: str
    role: str
    capabilities: list[str]
    risk_level: int = 1
    enabled: bool = True

DEFAULT_AGENTS = [
    AgentDefinition("supervisor", "Task analysis, delegation, escalation", ["analyze", "delegate", "coordinate"]),
    AgentDefinition("planner", "Task decomposition and dependency planning", ["plan", "decompose", "sequence"]),
    AgentDefinition("researcher", "Knowledge lookup and source assessment", ["research", "rag", "graph"]),
    AgentDefinition("executor", "Safe tool and workflow execution", ["execute", "tools", "workflows"], 2),
    AgentDefinition("reviewer", "Quality control and verification", ["review", "validate", "score"]),
    AgentDefinition("memory_curator", "Memory consolidation and graph update", ["memory", "graph", "summarize"]),
]

class AgentRegistry:
    def __init__(self, runtime_dir: str | Path):
        self.store = JsonStore(Path(runtime_dir) / "swarm_v124" / "agents.json", [])
        if not self.store.read():
            self.store.write([asdict(a) | {"registered_at": now_iso()} for a in DEFAULT_AGENTS])

    def list_agents(self) -> list[dict[str, Any]]:
        return self.store.read()

    def enabled_agents(self) -> list[dict[str, Any]]:
        return [a for a in self.list_agents() if a.get("enabled", True)]

    def get(self, name: str) -> dict[str, Any]:
        for agent in self.list_agents():
            if agent["name"] == name:
                return agent
        raise KeyError(f"Unknown swarm agent: {name}")

    def status(self) -> dict[str, Any]:
        agents = self.list_agents()
        return {"component": "swarm_agent_registry_v124", "agents": len(agents), "enabled": sum(1 for a in agents if a.get("enabled", True)), "healthy": True}
