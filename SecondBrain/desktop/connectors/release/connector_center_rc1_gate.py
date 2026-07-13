from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .connector_center_checklist import ConnectorCenterChecklist, ConnectorChecklistItem
from .connector_center_health_report import ConnectorCenterHealthReport
from .connector_center_metrics import ConnectorCenterMetrics
from .connector_center_validation import ConnectorCenterValidation, ConnectorValidationIssue


@dataclass(frozen=True)
class ConnectorCenterRC1Result:
    status: str
    checklist: list[ConnectorChecklistItem]
    metrics: ConnectorCenterMetrics
    issues: list[ConnectorValidationIssue]
    report: ConnectorCenterHealthReport

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "passed": self.passed,
            "checklist": [asdict(item) for item in self.checklist],
            "metrics": self.metrics.to_dict(),
            "issues": [asdict(issue) for issue in self.issues],
            "report": self.report.to_dict(),
        }


class ConnectorCenterRC1Gate:
    def __init__(self) -> None:
        self.checklist_builder = ConnectorCenterChecklist()
        self.validator = ConnectorCenterValidation()

    def run(self, available_capabilities: Iterable[str], metrics: ConnectorCenterMetrics | None = None) -> ConnectorCenterRC1Result:
        metrics = metrics or ConnectorCenterMetrics()
        checklist = self.checklist_builder.build(available_capabilities)
        issues = self.validator.validate(checklist, metrics)
        status = self.validator.status_from_issues(issues)
        report = ConnectorCenterHealthReport.build(status, checklist, metrics, issues)
        return ConnectorCenterRC1Result(status=status, checklist=checklist, metrics=metrics, issues=issues, report=report)

    def write_reports(self, result: ConnectorCenterRC1Result, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        files = {
            "connector_rc1_report": target / "connector_rc1_report.json",
            "connector_metrics": target / "connector_metrics.json",
            "connector_validation": target / "connector_validation.json",
            "connector_checklist": target / "connector_checklist.json",
        }
        files["connector_rc1_report"].write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        files["connector_metrics"].write_text(json.dumps(result.metrics.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        files["connector_validation"].write_text(json.dumps([asdict(issue) for issue in result.issues], indent=2, sort_keys=True), encoding="utf-8")
        files["connector_checklist"].write_text(json.dumps([asdict(item) for item in result.checklist], indent=2, sort_keys=True), encoding="utf-8")
        return files
