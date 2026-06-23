from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AgentHealthReport:
    status: str
    generated_at: str
    validation: list[dict[str, Any]]
    metrics: dict[str, Any]
    checklist: list[dict[str, Any]]
    blockers: list[str]

    @classmethod
    def build(cls, *, status: str, validation: list[Any], metrics: Any, checklist: list[Any]) -> "AgentHealthReport":
        validation_dicts = [asdict(item) for item in validation]
        checklist_dicts = [asdict(item) for item in checklist]
        blockers = [item["key"] for item in validation_dicts if item.get("status") in {"FAIL", "BLOCKED"}]
        return cls(
            status=status,
            generated_at=datetime.now(timezone.utc).isoformat(),
            validation=validation_dicts,
            metrics=metrics.to_dict() if hasattr(metrics, "to_dict") else dict(metrics),
            checklist=checklist_dicts,
            blockers=blockers,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
