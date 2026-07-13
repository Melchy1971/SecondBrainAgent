"""v30.63 Background Agents - persistence.

Three files under ``runtime/agent/background_agents/``:
* ``agents.json``      - the registry (one entry per agent).
* ``runs.jsonl``       - append-only run history.
* ``heartbeats.json``  - latest heartbeat per agent.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import AgentHeartbeat, AgentRun, BackgroundAgent


def base_dir(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "background_agents"


class BackgroundAgentStore:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.dir = base_dir(self.project_root)
        self.agents_path = self.dir / "agents.json"
        self.runs_path = self.dir / "runs.jsonl"
        self.heartbeats_path = self.dir / "heartbeats.json"

    # -- agents ------------------------------------------------------------
    def load_agents(self) -> dict[str, BackgroundAgent]:
        if not self.agents_path.exists():
            return {}
        try:
            raw = json.loads(self.agents_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {aid: BackgroundAgent.from_dict(data) for aid, data in raw.items()}

    def save_agents(self, agents: dict[str, BackgroundAgent]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        payload = {aid: agent.to_dict() for aid, agent in agents.items()}
        tmp = self.agents_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.agents_path)

    def get_agent(self, agent_id: str) -> BackgroundAgent | None:
        return self.load_agents().get(agent_id)

    def upsert_agent(self, agent: BackgroundAgent) -> BackgroundAgent:
        agents = self.load_agents()
        agents[agent.id] = agent
        self.save_agents(agents)
        return agent

    # -- runs --------------------------------------------------------------
    def append_run(self, run: AgentRun) -> AgentRun:
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.runs_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(run.to_dict(), ensure_ascii=False) + "\n")
        return run

    def runs(self, agent_id: str | None = None, *, limit: int = 100) -> list[AgentRun]:
        if not self.runs_path.exists():
            return []
        rows: list[AgentRun] = []
        for line in self.runs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent_id is None or data.get("agent_id") == agent_id:
                rows.append(AgentRun.from_dict(data))
        return rows[-max(1, int(limit)):]

    # -- heartbeats --------------------------------------------------------
    def load_heartbeats(self) -> dict[str, AgentHeartbeat]:
        if not self.heartbeats_path.exists():
            return {}
        try:
            raw = json.loads(self.heartbeats_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {aid: AgentHeartbeat.from_dict(data) for aid, data in raw.items()}

    def save_heartbeat(self, hb: AgentHeartbeat) -> AgentHeartbeat:
        self.dir.mkdir(parents=True, exist_ok=True)
        beats = self.load_heartbeats()
        beats[hb.agent_id] = hb
        payload = {aid: b.to_dict() for aid, b in beats.items()}
        tmp = self.heartbeats_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.heartbeats_path)
        return hb

    def get_heartbeat(self, agent_id: str) -> AgentHeartbeat | None:
        return self.load_heartbeats().get(agent_id)
