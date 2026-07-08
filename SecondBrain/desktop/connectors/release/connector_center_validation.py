from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .connector_center_checklist import ConnectorChecklistItem
from .connector_center_metrics import ConnectorCenterMetrics


@dataclass(frozen=True)
class ConnectorValidationIssue:
    severity: str
    code: str
    message: str


class ConnectorCenterValidation:
    def validate(
        self,
        checklist: Iterable[ConnectorChecklistItem],
        metrics: ConnectorCenterMetrics,
    ) -> list[ConnectorValidationIssue]:
        issues: list[ConnectorValidationIssue] = []
        for item in checklist:
            if item.required and item.status != "PASS":
                issues.append(ConnectorValidationIssue("FAIL", f"missing_{item.key}", f"Required capability missing: {item.label}"))

        if metrics.failed_jobs > 0:
            issues.append(ConnectorValidationIssue("WARNING", "failed_jobs_present", "Connector jobs contain failures"))
        if metrics.unavailable_connectors > 0:
            issues.append(ConnectorValidationIssue("FAIL", "connectors_unavailable", "One or more connectors are unavailable"))
        if metrics.total_connectors and metrics.enabled_connectors == 0:
            issues.append(ConnectorValidationIssue("WARNING", "no_enabled_connectors", "No connector is enabled"))
        return issues

    def status_from_issues(self, issues: Iterable[ConnectorValidationIssue]) -> str:
        severities = {issue.severity for issue in issues}
        if "FAIL" in severities:
            return "FAIL"
        if "BLOCKED" in severities:
            return "BLOCKED"
        if "WARNING" in severities:
            return "WARNING"
        return "PASS"
