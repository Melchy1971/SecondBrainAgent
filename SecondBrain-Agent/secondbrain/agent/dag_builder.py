"""v30.3 - DAG builder and topological sorting."""

from __future__ import annotations

from secondbrain.agent.workflow_models import WorkflowPlan, WorkflowStep


class WorkflowCycleError(ValueError):
    pass


class DagBuilder:
    def build(self, workflow_id: str, objective: str, steps: list[WorkflowStep]) -> WorkflowPlan:
        self.topological_order(steps)
        return WorkflowPlan(id=workflow_id, objective=objective, steps=steps)

    def topological_order(self, steps: list[WorkflowStep]) -> list[WorkflowStep]:
        by_id = {step.id: step for step in steps}
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[WorkflowStep] = []

        def visit(step_id: str) -> None:
            if step_id in visited:
                return
            if step_id in visiting:
                raise WorkflowCycleError(f"workflow cycle detected at step {step_id}")
            if step_id not in by_id:
                raise ValueError(f"missing dependency step: {step_id}")
            visiting.add(step_id)
            for dep in by_id[step_id].dependencies:
                visit(dep)
            visiting.remove(step_id)
            visited.add(step_id)
            ordered.append(by_id[step_id])

        for step in steps:
            visit(step.id)
        return ordered
