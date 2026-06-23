from __future__ import annotations

from .task_graph import AgentTask, TaskGraph


class AgentPlanner:
    """Deterministic task decomposition for agent goals."""

    def create_plan(self, goal: str, steps: list[str] | None = None) -> TaskGraph:
        clean_goal = goal.strip()
        if not clean_goal:
            raise ValueError("Goal must not be empty")
        step_titles = steps or [clean_goal]
        graph = TaskGraph()
        previous_id: str | None = None
        for idx, title in enumerate(step_titles, start=1):
            task = AgentTask(
                title=title.strip() or f"Step {idx}",
                description=f"Execute step {idx} for goal: {clean_goal}",
                dependencies=[previous_id] if previous_id else [],
                metadata={"goal": clean_goal, "step": idx},
                status="PLANNED",
            )
            graph.add(task)
            previous_id = task.task_id
        return graph
