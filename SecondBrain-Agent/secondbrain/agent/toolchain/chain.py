"""v30.70 ToolChain - container and fluent builder."""

from __future__ import annotations

from typing import Any

from .models import (
    ConditionalStep,
    LoopStep,
    ParallelStep,
    Step,
    ToolStep,
    new_id,
)


class ToolChain:
    def __init__(self, name: str = "chain", *, rollback_on_error: bool = True):
        self.id = new_id("chain")
        self.name = name
        self.steps: list[Step] = []
        self.rollback_on_error = rollback_on_error

    # -- fluent builders ---------------------------------------------------
    def add(self, step: Step) -> "ToolChain":
        self.steps.append(step)
        return self

    def tool(self, tool: str, *, name: str = "", inputs: dict | None = None, output_var: str = "",
             max_attempts: int = 1, fallback: Step | None = None, rollback_tool: str = "",
             rollback_inputs: dict | None = None) -> "ToolChain":
        return self.add(ToolStep.create(
            tool, name=name, inputs=inputs, output_var=output_var, max_attempts=max_attempts,
            fallback=fallback, rollback_tool=rollback_tool, rollback_inputs=rollback_inputs))

    def conditional(self, condition: Any, then_steps: list[Step],
                    else_steps: list[Step] | None = None, *, name: str = "if") -> "ToolChain":
        return self.add(ConditionalStep.create(condition, then_steps, else_steps, name=name))

    def loop_while(self, condition: Any, body: list[Step], *, max_iterations: int = 100,
                   name: str = "while") -> "ToolChain":
        return self.add(LoopStep.while_(condition, body, max_iterations=max_iterations, name=name))

    def foreach(self, items_var: str, body: list[Step], *, item_var: str = "item",
                name: str = "foreach") -> "ToolChain":
        return self.add(LoopStep.foreach(items_var, body, item_var=item_var, name=name))

    def parallel(self, branches: list[list[Step]], *, name: str = "parallel") -> "ToolChain":
        return self.add(ParallelStep.create(branches, name=name))

    # -- serialization / visualization ------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "rollback_on_error": self.rollback_on_error,
                "steps": [s.to_dict() for s in self.steps]}

    def visualize(self):
        from .visual import VisualWorkflow
        return VisualWorkflow(self)

    def run(self, executor, context: dict | None = None):
        return executor.run(self, context)
