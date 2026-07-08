"""Dashboard RC1 release gate.

The gate validates whether the dashboard foundation is coherent enough to be
promoted from feature slice to release candidate. It is intentionally pure and
framework-free so it can run in CI, CLI checks, and desktop diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class DashboardRCStatus(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    FAIL = "FAIL"


class DashboardRCSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


@dataclass(frozen=True)
class DashboardRCFinding:
    code: str
    severity: DashboardRCSeverity
    message: str
    component: str = "dashboard"
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "component": self.component,
            "message": self.message,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class DashboardRCSnapshot:
    widgets: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    layout: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    actions: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    services: Mapping[str, bool] = field(default_factory=dict)
    tests: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DashboardRCReport:
    status: DashboardRCStatus
    score: int
    findings: tuple[DashboardRCFinding, ...]
    summary: dict[str, Any]

    @property
    def blockers(self) -> tuple[DashboardRCFinding, ...]:
        return tuple(f for f in self.findings if f.severity == DashboardRCSeverity.BLOCKER)

    @property
    def warnings(self) -> tuple[DashboardRCFinding, ...]:
        return tuple(f for f in self.findings if f.severity == DashboardRCSeverity.WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "score": self.score,
            "summary": dict(self.summary),
            "findings": [finding.to_dict() for finding in self.findings],
        }


REQUIRED_WIDGETS = {
    "recent_imports",
    "running_jobs",
    "connector_health",
    "rag_status",
    "system_health",
    "recent_errors",
    "workspace_summary",
}

REQUIRED_SERVICES = {
    "dashboard_service",
    "widget_registry",
    "widget_manager",
    "refresh_scheduler",
    "dashboard_persistence",
}

REQUIRED_ACTIONS = {
    "refresh_widget",
    "open_widget_details",
    "disable_widget",
}


def _missing(required: Iterable[str], available: Mapping[str, Any]) -> list[str]:
    return sorted(set(required) - set(available.keys()))


def evaluate_dashboard_rc(snapshot: DashboardRCSnapshot) -> DashboardRCReport:
    findings: list[DashboardRCFinding] = []

    missing_widgets = _missing(REQUIRED_WIDGETS, snapshot.widgets)
    if missing_widgets:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_MISSING_WIDGETS",
                severity=DashboardRCSeverity.BLOCKER,
                component="widgets",
                message="Required dashboard widgets are missing.",
                evidence={"missing": missing_widgets},
            )
        )

    disabled_required = sorted(
        widget_id
        for widget_id in REQUIRED_WIDGETS.intersection(snapshot.widgets.keys())
        if snapshot.widgets[widget_id].get("enabled") is False
    )
    if disabled_required:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_REQUIRED_WIDGET_DISABLED",
                severity=DashboardRCSeverity.WARNING,
                component="widgets",
                message="Required widgets exist but are disabled.",
                evidence={"disabled": disabled_required},
            )
        )

    missing_services = sorted(name for name in REQUIRED_SERVICES if snapshot.services.get(name) is not True)
    if missing_services:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_MISSING_SERVICES",
                severity=DashboardRCSeverity.BLOCKER,
                component="services",
                message="Required dashboard services are unavailable.",
                evidence={"missing": missing_services},
            )
        )

    missing_actions = _missing(REQUIRED_ACTIONS, snapshot.actions)
    if missing_actions:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_MISSING_ACTIONS",
                severity=DashboardRCSeverity.WARNING,
                component="actions",
                message="Recommended dashboard actions are missing.",
                evidence={"missing": missing_actions},
            )
        )

    layout_widget_ids = {value.get("widget_id") for value in snapshot.layout.values()}
    orphan_layout_entries = sorted(str(value.get("widget_id")) for value in snapshot.layout.values() if value.get("widget_id") not in snapshot.widgets)
    widgets_without_layout = sorted(REQUIRED_WIDGETS.intersection(snapshot.widgets.keys()) - layout_widget_ids)

    if orphan_layout_entries:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_LAYOUT_ORPHANS",
                severity=DashboardRCSeverity.BLOCKER,
                component="layout",
                message="Layout references unknown widgets.",
                evidence={"orphan_widget_ids": orphan_layout_entries},
            )
        )

    if widgets_without_layout:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_WIDGETS_WITHOUT_LAYOUT",
                severity=DashboardRCSeverity.WARNING,
                component="layout",
                message="Required widgets are not placed in the dashboard layout.",
                evidence={"widget_ids": widgets_without_layout},
            )
        )

    tests_passed = int(snapshot.tests.get("passed", 0) or 0)
    tests_failed = int(snapshot.tests.get("failed", 0) or 0)
    if tests_failed > 0:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_TEST_FAILURES",
                severity=DashboardRCSeverity.BLOCKER,
                component="tests",
                message="Dashboard test suite has failures.",
                evidence={"failed": tests_failed, "passed": tests_passed},
            )
        )
    elif tests_passed <= 0:
        findings.append(
            DashboardRCFinding(
                code="DASHBOARD_TESTS_NOT_REPORTED",
                severity=DashboardRCSeverity.WARNING,
                component="tests",
                message="No dashboard test result was reported.",
                evidence=dict(snapshot.tests),
            )
        )

    blocker_count = sum(1 for f in findings if f.severity == DashboardRCSeverity.BLOCKER)
    warning_count = sum(1 for f in findings if f.severity == DashboardRCSeverity.WARNING)
    score = max(0, 100 - blocker_count * 35 - warning_count * 10)

    if blocker_count:
        status = DashboardRCStatus.FAIL
    elif warning_count:
        status = DashboardRCStatus.CONDITIONAL_PASS
    else:
        status = DashboardRCStatus.PASS

    summary = {
        "required_widgets": len(REQUIRED_WIDGETS),
        "widgets_present": len(REQUIRED_WIDGETS.intersection(snapshot.widgets.keys())),
        "services_required": len(REQUIRED_SERVICES),
        "services_available": sum(1 for name in REQUIRED_SERVICES if snapshot.services.get(name) is True),
        "actions_required": len(REQUIRED_ACTIONS),
        "actions_available": len(REQUIRED_ACTIONS.intersection(snapshot.actions.keys())),
        "layout_entries": len(snapshot.layout),
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "blockers": blocker_count,
        "warnings": warning_count,
    }
    return DashboardRCReport(status=status, score=score, findings=tuple(findings), summary=summary)


class DashboardRCGate:
    def evaluate(self, snapshot: DashboardRCSnapshot) -> DashboardRCReport:
        return evaluate_dashboard_rc(snapshot)
