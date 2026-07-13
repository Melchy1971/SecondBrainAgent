
from __future__ import annotations
from typing import Any

class MemoryCuratorAgent:
    name = "memory_curator"

    def curate(self, task: str, context: dict[str, Any], graph_engine: Any | None = None) -> dict[str, Any]:
        summary = f"Swarm bearbeitete Aufgabe: {task}"
        graph_result = None
        if graph_engine is not None:
            try:
                graph_result = graph_engine.ingest_text(summary, source_id=context.get("task_id", "swarm"), title="Swarm Result")
            except Exception as exc:
                graph_result = {"error": str(exc)}
        return {
            "agent": self.name,
            "summary": summary,
            "graph_result": graph_result,
            "persisted": graph_result is not None and "error" not in graph_result,
        }
