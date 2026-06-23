"""Search RC1 validation primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class SearchCheckStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class SearchValidationCheck:
    name: str
    status: SearchCheckStatus
    message: str = ""
    critical: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchValidationReport:
    checks: tuple[SearchValidationCheck, ...]

    @property
    def status(self) -> SearchCheckStatus:
        statuses = {check.status for check in self.checks}
        if SearchCheckStatus.BLOCKED in statuses:
            return SearchCheckStatus.BLOCKED
        if any(check.critical and check.status == SearchCheckStatus.FAIL for check in self.checks):
            return SearchCheckStatus.FAIL
        if SearchCheckStatus.FAIL in statuses:
            return SearchCheckStatus.WARNING
        if SearchCheckStatus.WARNING in statuses:
            return SearchCheckStatus.WARNING
        return SearchCheckStatus.PASS

    @property
    def blockers(self) -> tuple[SearchValidationCheck, ...]:
        return tuple(c for c in self.checks if c.status == SearchCheckStatus.BLOCKED or (c.critical and c.status == SearchCheckStatus.FAIL))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "critical": c.critical,
                    "metadata": c.metadata,
                }
                for c in self.checks
            ],
            "blockers": [c.name for c in self.blockers],
        }


def validate_required_capabilities(capabilities: dict[str, bool]) -> SearchValidationReport:
    required = (
        "search_service",
        "hybrid_search",
        "preview",
        "highlighting",
        "saved_searches",
        "persistence",
        "history",
    )
    checks: list[SearchValidationCheck] = []
    for name in required:
        available = bool(capabilities.get(name, False))
        checks.append(
            SearchValidationCheck(
                name=name,
                status=SearchCheckStatus.PASS if available else SearchCheckStatus.FAIL,
                message="available" if available else "missing required search capability",
                critical=True,
            )
        )
    return SearchValidationReport(tuple(checks))


def merge_reports(reports: Iterable[SearchValidationReport]) -> SearchValidationReport:
    checks: list[SearchValidationCheck] = []
    for report in reports:
        checks.extend(report.checks)
    return SearchValidationReport(tuple(checks))
