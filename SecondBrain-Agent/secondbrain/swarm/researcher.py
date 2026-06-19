
from __future__ import annotations
from typing import Any

class ResearchAgent:
    name = "researcher"

    def research(self, task: str, context: dict[str, Any], graph_engine: Any | None = None) -> dict[str, Any]:
        findings = []
        if graph_engine is not None:
            try:
                findings = graph_engine.search_entities(task, 8)
            except Exception as exc:
                findings = [{"error": str(exc)}]
        return {
            "agent": self.name,
            "summary": f"Recherchekontext für: {task}",
            "findings": findings,
            "confidence": 0.65 if findings else 0.4,
        }
