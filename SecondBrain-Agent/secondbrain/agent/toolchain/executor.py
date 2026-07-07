"""v30.70 ToolChain - executor.

Runs a ToolChain with control flow and resilience. Tools are invoked through the
existing ``ToolRegistry`` (or an injected runner). Failure handling per tool step:
retry -> fallback -> (chain) rollback of completed compensable steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .models import (
    FAILED,
    OK,
    SKIPPED,
    ChainContext,
    ChainRun,
    ConditionalStep,
    LoopStep,
    ParallelStep,
    Step,
    StepResult,
    ToolStep,
    eval_condition,
)


class StepFailure(Exception):
    def __init__(self, step_id: str, error: str):
        super().__init__(error)
        self.step_id = step_id
        self.error = error


class ToolChainExecutor:
    def __init__(self, project_root: str | Path | None = None, *, registry: Any | None = None,
                 tool_runner: Callable[[str, dict], Any] | None = None,
                 approved: bool = True):
        self.project_root = Path(project_root).resolve() if project_root else None
        self._registry = registry
        self._tool_runner = tool_runner
        self.approved = approved

    # -- tool invocation (reuse ToolRegistry) -----------------------------
    def _registry_lazy(self):
        if self._registry is not None:
            return self._registry
        if self.project_root is None:
            return None
        from secondbrain.agent.tool_registry import ToolRegistry
        self._registry = ToolRegistry(self.project_root / "runtime" / "tools_v121")
        return self._registry

    def invoke_tool(self, name: str, inputs: dict) -> Any:
        if self._tool_runner is not None:
            return self._tool_runner(name, inputs)
        registry = self._registry_lazy()
        if registry is None:
            raise RuntimeError(f"no_tool_runtime_for:{name}")
        result = registry.run(name, inputs, approved=self.approved)
        if getattr(result, "success", False):
            return getattr(result, "output", None)
        raise RuntimeError(getattr(result, "error", None) or f"tool_failed:{name}")

    # -- entry -------------------------------------------------------------
    def run(self, chain, context: ChainContext | dict | None = None) -> ChainRun:
        ctx = context if isinstance(context, ChainContext) else ChainContext(context)
        run = ChainRun(chain_id=getattr(chain, "id", "chain"), status=OK)
        rollback_stack: list[tuple[str, dict]] = []
        steps = getattr(chain, "steps", chain)
        try:
            self._run_steps(steps, ctx, run, rollback_stack)
            run.status = OK
        except StepFailure as exc:
            run.status = FAILED
            run.error = f"{exc.step_id}: {exc.error}"
            if getattr(chain, "rollback_on_error", True):
                self._rollback(rollback_stack, ctx, run)
        run.context = ctx.to_dict()
        return run

    # -- step dispatch -----------------------------------------------------
    def _run_steps(self, steps: list[Step], ctx: ChainContext, run: ChainRun,
                   rollback_stack: list) -> None:
        for step in steps:
            self._run_step(step, ctx, run, rollback_stack)

    def _run_step(self, step: Step, ctx: ChainContext, run: ChainRun, rollback_stack: list) -> None:
        if isinstance(step, ToolStep):
            self._run_tool_step(step, ctx, run, rollback_stack)
        elif isinstance(step, ConditionalStep):
            branch = step.then_steps if eval_condition(step.condition, ctx) else step.else_steps
            run.results.append(StepResult(step.id, step.name, step.type, OK,
                                          output={"branch": "then" if branch is step.then_steps else "else"}))
            self._run_steps(branch, ctx, run, rollback_stack)
        elif isinstance(step, LoopStep):
            self._run_loop(step, ctx, run, rollback_stack)
        elif isinstance(step, ParallelStep):
            self._run_parallel(step, ctx, run, rollback_stack)
        else:  # pragma: no cover - unknown step
            raise StepFailure(getattr(step, "id", "?"), "unknown_step_type")

    def _run_tool_step(self, step: ToolStep, ctx: ChainContext, run: ChainRun,
                       rollback_stack: list) -> None:
        inputs = ctx.resolve(step.inputs)
        attempts = 0
        last_error = ""
        for attempts in range(1, max(1, step.retry.max_attempts) + 1):
            try:
                output = self.invoke_tool(step.tool, inputs)
                if step.output_var:
                    ctx.set(step.output_var, output)
                run.results.append(StepResult(step.id, step.name, step.type, OK,
                                              output=output, attempts=attempts))
                if step.rollback_tool:
                    rollback_stack.append((step.rollback_tool, ctx.resolve(step.rollback_inputs) or inputs))
                return
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
        # retries exhausted -> fallback
        if step.fallback is not None:
            try:
                self._run_step(step.fallback, ctx, run, rollback_stack)
                # mark the original as fallback-recovered
                run.results.append(StepResult(step.id, step.name, step.type, OK,
                                              attempts=attempts, used_fallback=True))
                return
            except StepFailure:
                pass
        run.results.append(StepResult(step.id, step.name, step.type, FAILED,
                                      error=last_error, attempts=attempts))
        raise StepFailure(step.id, last_error)

    def _run_loop(self, step: LoopStep, ctx: ChainContext, run: ChainRun, rollback_stack: list) -> None:
        iterations = 0
        if step.mode == "foreach":
            items = ctx.get(step.items_var) or []
            for item in items:
                if iterations >= step.max_iterations:
                    break
                ctx.set(step.item_var, item)
                self._run_steps(step.body, ctx, run, rollback_stack)
                iterations += 1
        else:  # while
            while eval_condition(step.condition, ctx):
                if iterations >= step.max_iterations:
                    break
                self._run_steps(step.body, ctx, run, rollback_stack)
                iterations += 1
        run.results.append(StepResult(step.id, step.name, step.type, OK,
                                      output={"iterations": iterations}))

    def _run_parallel(self, step: ParallelStep, ctx: ChainContext, run: ChainRun,
                      rollback_stack: list) -> None:
        # Branches are independent; executed deterministically in order and
        # gathered. A failure in any branch fails the parallel step.
        for branch in step.branches:
            self._run_steps(branch, ctx, run, rollback_stack)
        run.results.append(StepResult(step.id, step.name, step.type, OK,
                                      output={"branches": len(step.branches)}))

    # -- rollback ----------------------------------------------------------
    def _rollback(self, rollback_stack: list, ctx: ChainContext, run: ChainRun) -> None:
        for tool, inputs in reversed(rollback_stack):
            try:
                self.invoke_tool(tool, inputs)
                run.rolled_back.append(tool)
            except Exception:
                # best-effort compensation; record what we could undo
                continue
