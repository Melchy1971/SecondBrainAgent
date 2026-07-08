from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DesktopRCStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class DesktopRCStatusSnapshot:
    status: DesktopRCStatus
    checked_at: str
    components: dict[str, DesktopRCStatus] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_components(
        cls,
        components: dict[str, DesktopRCStatus | str],
        metrics: dict[str, Any] | None = None,
    ) -> "DesktopRCStatusSnapshot":
        normalized = {key: DesktopRCStatus(value) for key, value in components.items()}
        status = DesktopRCStatus.PASS
        if any(value == DesktopRCStatus.FAIL for value in normalized.values()):
            status = DesktopRCStatus.FAIL
        elif any(value == DesktopRCStatus.WARNING for value in normalized.values()):
            status = DesktopRCStatus.WARNING
        return cls(
            status=status,
            checked_at=datetime.now(timezone.utc).isoformat(),
            components=normalized,
            metrics=dict(metrics or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checked_at": self.checked_at,
            "components": {key: value.value for key, value in self.components.items()},
            "metrics": dict(self.metrics),
        }
