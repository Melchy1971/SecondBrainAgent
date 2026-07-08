from __future__ import annotations

from dataclasses import dataclass, field

from .flow_models import FlowStep


@dataclass
class DesktopFlow:
    flow_id: str
    title: str
    steps: list[FlowStep]
    description: str = ""

    def validate(self) -> None:
        if not self.flow_id.strip():
            raise ValueError("flow_id must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.steps:
            raise ValueError("flow must contain at least one step")
        seen: set[str] = set()
        for step in self.steps:
            step.validate()
            if step.step_id in seen:
                raise ValueError(f"duplicate step_id: {step.step_id}")
            seen.add(step.step_id)


@dataclass
class DesktopFlowRegistry:
    _flows: dict[str, DesktopFlow] = field(default_factory=dict)

    def register(self, flow: DesktopFlow) -> None:
        flow.validate()
        if flow.flow_id in self._flows:
            raise ValueError(f"flow already registered: {flow.flow_id}")
        self._flows[flow.flow_id] = flow

    def get(self, flow_id: str) -> DesktopFlow:
        try:
            return self._flows[flow_id]
        except KeyError as exc:
            raise KeyError(f"unknown flow: {flow_id}") from exc

    def list_flows(self) -> list[DesktopFlow]:
        return sorted(self._flows.values(), key=lambda flow: flow.flow_id)
