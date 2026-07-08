"""v30.70 ToolChain - Visual Workflow.

Renders a ToolChain as a Mermaid flowchart and as an indented ASCII tree, so a
composed tool workflow can be inspected before it runs.
"""

from __future__ import annotations

from typing import Any

from .models import (
    STEP_CONDITIONAL,
    STEP_LOOP,
    STEP_PARALLEL,
    STEP_TOOL,
    ConditionalStep,
    LoopStep,
    ParallelStep,
    Step,
    ToolStep,
)


class VisualWorkflow:
    def __init__(self, chain):
        self.chain = chain

    # -- ASCII tree --------------------------------------------------------
    def ascii(self) -> str:
        lines: list[str] = [f"ToolChain: {getattr(self.chain, 'name', 'chain')}"]
        for step in getattr(self.chain, "steps", []):
            self._ascii_step(step, 1, lines)
        return "\n".join(lines)

    def _ascii_step(self, step: Step, depth: int, lines: list[str]) -> None:
        pad = "  " * depth
        if isinstance(step, ToolStep):
            extra = []
            if step.retry.max_attempts > 1:
                extra.append(f"retry x{step.retry.max_attempts}")
            if step.fallback:
                extra.append("fallback")
            if step.rollback_tool:
                extra.append(f"rollback:{step.rollback_tool}")
            suffix = f" [{', '.join(extra)}]" if extra else ""
            lines.append(f"{pad}- tool:{step.tool}{suffix}")
        elif isinstance(step, ConditionalStep):
            lines.append(f"{pad}- if {step.name}")
            lines.append(f"{pad}  then:")
            for s in step.then_steps:
                self._ascii_step(s, depth + 2, lines)
            if step.else_steps:
                lines.append(f"{pad}  else:")
                for s in step.else_steps:
                    self._ascii_step(s, depth + 2, lines)
        elif isinstance(step, LoopStep):
            head = f"foreach {step.items_var}" if step.mode == "foreach" else "while"
            lines.append(f"{pad}- loop ({head})")
            for s in step.body:
                self._ascii_step(s, depth + 1, lines)
        elif isinstance(step, ParallelStep):
            lines.append(f"{pad}- parallel ({len(step.branches)} branches)")
            for i, branch in enumerate(step.branches):
                lines.append(f"{pad}  branch {i + 1}:")
                for s in branch:
                    self._ascii_step(s, depth + 2, lines)

    # -- Mermaid -----------------------------------------------------------
    def mermaid(self) -> str:
        lines = ["flowchart TD"]
        prev = "start([start])"
        lines.append(f"    {prev}")
        for step in getattr(self.chain, "steps", []):
            prev = self._mermaid_step(step, prev, lines)
        lines.append(f"    {prev} --> done([done])")
        return "\n".join(lines)

    def _node(self, step: Step) -> str:
        nid = step.id.replace("-", "_")
        if step.type == STEP_TOOL:
            return f"{nid}[\"{step.name}\"]"
        if step.type == STEP_CONDITIONAL:
            return f"{nid}{{\"{step.name}\"}}"
        if step.type == STEP_LOOP:
            return f"{nid}[[\"{step.name}\"]]"
        if step.type == STEP_PARALLEL:
            return f"{nid}[/\"{step.name}\"/]"
        return f"{nid}[\"{step.name}\"]"

    def _mermaid_step(self, step: Step, prev: str, lines: list[str]) -> str:
        node = self._node(step)
        nid = node.split("[")[0].split("{")[0].split("(")[0]
        lines.append(f"    {prev} --> {node}")
        if isinstance(step, ConditionalStep):
            last = nid
            for label, branch in (("then", step.then_steps), ("else", step.else_steps)):
                p = f"{nid}"
                for s in branch:
                    p = self._mermaid_step(s, p, lines)
                if branch:
                    last = p
            return last
        if isinstance(step, LoopStep):
            p = nid
            for s in step.body:
                p = self._mermaid_step(s, p, lines)
            lines.append(f"    {p} -.loop.-> {nid}")
            return nid
        if isinstance(step, ParallelStep):
            joins = []
            for branch in step.branches:
                p = nid
                for s in branch:
                    p = self._mermaid_step(s, p, lines)
                joins.append(p)
            return joins[-1] if joins else nid
        return nid

    def to_dict(self) -> dict[str, Any]:
        return {"ascii": self.ascii(), "mermaid": self.mermaid(),
                "chain": self.chain.to_dict() if hasattr(self.chain, "to_dict") else {}}
