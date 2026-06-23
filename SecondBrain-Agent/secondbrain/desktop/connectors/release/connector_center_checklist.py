from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ConnectorChecklistItem:
    key: str
    label: str
    required: bool = True
    status: str = "UNKNOWN"
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


class ConnectorCenterChecklist:
    REQUIRED_KEYS = (
        "center_service",
        "connector_registry",
        "configuration",
        "secret_references",
        "sync_actions",
        "job_monitoring",
        "health_snapshot",
        "error_reporting",
    )

    def build(self, available: Iterable[str]) -> list[ConnectorChecklistItem]:
        available_set = set(available)
        items: list[ConnectorChecklistItem] = []
        for key in self.REQUIRED_KEYS:
            status = "PASS" if key in available_set else "FAIL"
            detail = "available" if status == "PASS" else "missing"
            items.append(ConnectorChecklistItem(key=key, label=key.replace("_", " ").title(), status=status, detail=detail))
        return items

    def summarize(self, items: Iterable[ConnectorChecklistItem]) -> dict[str, int]:
        counts = {"PASS": 0, "WARNING": 0, "FAIL": 0, "BLOCKED": 0, "UNKNOWN": 0}
        for item in items:
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts
