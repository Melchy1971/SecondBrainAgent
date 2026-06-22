"""P2 v21.0 - Planner Foundation."""

from secondbrain.agent.task_graph import TaskGraph, TaskNode


class Planner:
    def create_plan(self, objective: str):
        graph = TaskGraph()
        graph.add(TaskNode("objective", objective))
        return graph
