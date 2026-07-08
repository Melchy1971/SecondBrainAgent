from __future__ import annotations

from .task_graph import AgentTask, TaskGraph


class ReplanEngine:
    def replan_failed(self, graph: TaskGraph, reason: str = "retry") -> TaskGraph:
        new_graph = TaskGraph.from_dict(graph.to_dict())
        failed = [task for task in new_graph.tasks.values() if task.status == "FAILED"]
        for task in failed:
            retry_task = AgentTask(
                title=f"Retry: {task.title}",
                description=f"Replanned after failure: {reason}",
                dependencies=list(task.dependencies),
                tool_calls=list(task.tool_calls),
                metadata={**task.metadata, "replanned_from": task.task_id, "reason": reason},
                status="REPLANNED",
            )
            new_graph.add(retry_task)
        return new_graph
