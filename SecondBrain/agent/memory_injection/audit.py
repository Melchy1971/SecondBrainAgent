"""v30.64 Agent Memory Injection - audit trail.

Append-only JSONL of every injection, so what an agent was actually fed (and
what was withheld and why) is reconstructable after the fact.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

AUDIT_SCHEMA = "secondbrain.agent.memory_injection.audit.v30_64"


def audit_path(root: str | Path) -> Path:
    return Path(root).resolve() / "runtime" / "agent" / "memory_injection" / "audit.jsonl"


class MemoryInjectionAudit:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.path = audit_path(self.project_root)

    def record(self, *, actor: str, agent_id: str, context) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        ctx = context.to_dict()
        entry = {
            "schema": AUDIT_SCHEMA,
            "id": uuid4().hex[:16],
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "actor": actor,
            "agent_id": agent_id,
            "privacy_mode": ctx["privacy_mode"],
            "query": ctx["query"],
            "injected_memory_ids": [e["memory_id"] for e in ctx["evidences"]],
            "sources": ctx["sources"],
            "exclusions": ctx["exclusions"],
            "conflicts": ctx["conflicts"],
            "budget": ctx["budget"],
            "counts": ctx["counts"],
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def events(self, agent_id: str | None = None, *, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent_id is None or row.get("agent_id") == agent_id:
                rows.append(row)
        return rows[-max(1, int(limit)):]
