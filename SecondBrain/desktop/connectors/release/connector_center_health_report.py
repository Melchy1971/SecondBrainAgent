from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable

from .connector_center_checklist import ConnectorChecklistItem, ConnectorCenterChecklist
from .connector_center_metrics import ConnectorCenterMetrics
from .connector_center_validation import ConnectorValidationIssue


@dataclass(frozen=True)
class ConnectorCenterHealthReport:
    status: str
    generated_at: str
    checklist_summary: dict[str, int]
    metrics: dict[str, int | float | bool]
    issues: list[dict[str, str]]

    @classmethod
    def build(
        cls,
        status: str,
        checklist: Iterable[ConnectorChecklistItem],
        metrics: ConnectorCenterMetrics,
        issues: Iterable[ConnectorValidationIssue],
    ) -> "ConnectorCenterHealthReport":
        checklist_list = list(checklist)
        return cls(
            status=status,
            generated_at=datetime.now(timezone.utc).isoformat(),
            checklist_summary=ConnectorCenterChecklist().summarize(checklist_list),
            metrics=metrics.to_dict(),
            issues=[asdict(issue) for issue in issues],
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
