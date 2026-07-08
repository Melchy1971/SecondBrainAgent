"""Search RC1 gate orchestration."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .search_checklist import build_default_search_checklist
from .search_health_report import SearchHealthReport, create_search_health_report
from .search_metrics import SearchMetricsSnapshot
from .search_validation import SearchCheckStatus, validate_required_capabilities


@dataclass(frozen=True)
class SearchRC1GateInput:
    version: str
    capabilities: dict[str, bool]
    checklist_flags: dict[str, bool]
    metrics: SearchMetricsSnapshot


@dataclass(frozen=True)
class SearchRC1GateResult:
    status: SearchCheckStatus
    report: SearchHealthReport

    @property
    def passed(self) -> bool:
        return self.status == SearchCheckStatus.PASS

    def to_dict(self) -> dict[str, object]:
        data = self.report.to_dict()
        data["passed"] = self.passed
        return data


class SearchRC1Gate:
    def evaluate(self, gate_input: SearchRC1GateInput) -> SearchRC1GateResult:
        validation = validate_required_capabilities(gate_input.capabilities)
        checklist = build_default_search_checklist(gate_input.checklist_flags)
        report = create_search_health_report(
            version=gate_input.version,
            validation=validation,
            checklist=checklist,
            metrics=gate_input.metrics,
        )
        return SearchRC1GateResult(status=report.status, report=report)

    def write_reports(self, result: SearchRC1GateResult, output_dir: str | Path) -> dict[str, Path]:
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        payload = result.to_dict()
        files = {
            "search_rc1_report": target / "search_rc1_report.json",
            "search_metrics": target / "search_metrics.json",
            "search_validation": target / "search_validation.json",
            "search_checklist": target / "search_checklist.json",
        }
        files["search_rc1_report"].write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        files["search_metrics"].write_text(json.dumps(payload["metrics"], indent=2, sort_keys=True), encoding="utf-8")
        files["search_validation"].write_text(json.dumps(payload["validation"], indent=2, sort_keys=True), encoding="utf-8")
        files["search_checklist"].write_text(json.dumps(payload["checklist"], indent=2, sort_keys=True), encoding="utf-8")
        return files
