
from __future__ import annotations
from typing import Any
import re
from .common import new_id, now_iso

class PlannerAgent:
    name = "planner"

    def decompose(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = task.strip()
        steps = []
        lowered = text.lower()
        if any(x in lowered for x in ["recherch", "suche", "analyse", "vergleich", "research"]):
            steps.append({"id": "research", "agent": "researcher", "action": "research", "depends_on": []})
        steps.append({"id": "execute", "agent": "executor", "action": "execute", "depends_on": ["research"] if steps else []})
        steps.append({"id": "review", "agent": "reviewer", "action": "review", "depends_on": ["execute"]})
        steps.append({"id": "memorize", "agent": "memory_curator", "action": "curate", "depends_on": ["review"]})
        complexity = min(5, max(1, len(re.findall(r"\w+", text)) // 12 + len(steps) // 2))
        return {"plan_id": new_id("plan"), "task": task, "steps": steps, "complexity": complexity, "created_at": now_iso()}
