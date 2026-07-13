from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .flow_models import FlowResult, FlowStatus, StepResult, utc_now
from .flow_registry import DesktopFlowRegistry


@dataclass
class DesktopFlowRunner:
    registry: DesktopFlowRegistry
    events: list[dict[str, Any]] = field(default_factory=list)

    def run(self, flow_id: str, initial_context: dict[str, Any] | None = None) -> FlowResult:
        flow = self.registry.get(flow_id)
        context: dict[str, Any] = dict(initial_context or {})
        started_at = utc_now()
        self._emit("FLOW_STARTED", flow_id=flow_id)
        step_results: list[StepResult] = []
        overall = FlowStatus.PASSED

        for step in flow.steps:
            step_started = utc_now()
            self._emit("FLOW_STEP_STARTED", flow_id=flow_id, step_id=step.step_id)
            try:
                output = step.action(context)
                if isinstance(output, dict):
                    context.update(output)
                result = StepResult(
                    step_id=step.step_id,
                    name=step.name,
                    status=FlowStatus.PASSED,
                    output=output,
                    started_at=step_started,
                    finished_at=utc_now(),
                )
                self._emit("FLOW_STEP_PASSED", flow_id=flow_id, step_id=step.step_id)
            except Exception as exc:  # deliberate boundary for GUI flow safety
                result = StepResult(
                    step_id=step.step_id,
                    name=step.name,
                    status=FlowStatus.FAILED,
                    error=str(exc),
                    started_at=step_started,
                    finished_at=utc_now(),
                )
                step_results.append(result)
                self._emit("FLOW_STEP_FAILED", flow_id=flow_id, step_id=step.step_id, error=str(exc))
                if step.required:
                    overall = FlowStatus.FAILED
                    break
                overall = FlowStatus.FAILED
                continue
            step_results.append(result)

        finished_at = utc_now()
        self._emit("FLOW_COMPLETED" if overall == FlowStatus.PASSED else "FLOW_FAILED", flow_id=flow_id)
        return FlowResult(flow_id=flow_id, status=overall, steps=step_results, context=context, started_at=started_at, finished_at=finished_at)

    def _emit(self, event_type: str, **payload: Any) -> None:
        self.events.append({"type": event_type, **payload})
