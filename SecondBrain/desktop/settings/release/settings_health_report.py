from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SettingsHealthReport:
    status: str
    checks: dict[str, str] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_checks(cls, checks: dict[str, str]) -> "SettingsHealthReport":
        if any(value in {"FAIL", "BLOCKED"} for value in checks.values()):
            status = "FAIL"
        elif any(value == "WARNING" for value in checks.values()):
            status = "WARNING"
        else:
            status = "PASS"
        return cls(status=status, checks=dict(checks))

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": dict(self.checks),
            "generated_at": self.generated_at,
        }
