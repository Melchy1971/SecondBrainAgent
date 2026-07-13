from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Iterable, Any

from .agent_checklist import AgentChecklist
from .agent_health_report import AgentHealthReport
from .agent_metrics import AgentMetrics, AgentMetricsSnapshot
from .agent_validation import AgentValidation, AgentValidationItem


@dataclass(frozen=True)
class AgentRC1GateResult:
    status: str
    validation: list[AgentValidationItem]
    metrics: AgentMetricsSnapshot
    checklist_complete: bool
    blockers: list[str]
    report: AgentHealthReport

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


class AgentRC1Gate:
    """Aggregates Agent RC1 release checks into one deterministic gate result."""

    def __init__(
        self,
        validation: AgentValidation | None = None,
        checklist: AgentChecklist | None = None,
        metrics: AgentMetrics | None = None,
    ) -> None:
        self.validation = validation or AgentValidation()
        self.checklist = checklist or AgentChecklist()
        self.metrics = metrics or AgentMetrics()

    def run(
        self,
        *,
        capabilities: Mapping[str, bool],
        checklist_passed: Iterable[str],
        metric_inputs: Mapping[str, Any] | None = None,
    ) -> AgentRC1GateResult:
        validation_items = self.validation.validate(capabilities)
        checklist_items = self.checklist.build(checklist_passed)
        checklist_complete = self.checklist.complete(checklist_items)
        metric_inputs = dict(metric_inputs or {})
        metrics_snapshot = self.metrics.snapshot(**metric_inputs)

        blockers = [item.key for item in validation_items if item.blocking]
        if not checklist_complete:
            blockers.append("checklist_incomplete")

        status = "PASS" if not blockers else "BLOCKED"
        report = AgentHealthReport.build(
            status=status,
            validation=validation_items,
            metrics=metrics_snapshot,
            checklist=checklist_items,
        )
        return AgentRC1GateResult(
            status=status,
            validation=validation_items,
            metrics=metrics_snapshot,
            checklist_complete=checklist_complete,
            blockers=blockers,
            report=report,
        )
