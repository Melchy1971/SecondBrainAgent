"""Composable Search RC1 health report."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .search_checklist import SearchChecklist
from .search_metrics import SearchMetricsSnapshot
from .search_validation import SearchCheckStatus, SearchValidationReport


@dataclass(frozen=True)
class SearchHealthReport:
    version: str
    generated_at: str
    validation: SearchValidationReport
    checklist: SearchChecklist
    metrics: SearchMetricsSnapshot

    @property
    def status(self) -> SearchCheckStatus:
        if self.validation.status in {SearchCheckStatus.BLOCKED, SearchCheckStatus.FAIL}:
            return self.validation.status
        if not self.checklist.complete:
            return SearchCheckStatus.BLOCKED
        return self.validation.status

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "status": self.status.value,
            "validation": self.validation.to_dict(),
            "checklist": self.checklist.to_dict(),
            "metrics": self.metrics.to_dict(),
        }


def create_search_health_report(
    *,
    version: str,
    validation: SearchValidationReport,
    checklist: SearchChecklist,
    metrics: SearchMetricsSnapshot,
) -> SearchHealthReport:
    return SearchHealthReport(
        version=version,
        generated_at=datetime.now(timezone.utc).isoformat(),
        validation=validation,
        checklist=checklist,
        metrics=metrics,
    )
