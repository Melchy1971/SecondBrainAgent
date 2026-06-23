from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class GuiHealthReport:
    modules_ready: int = 0
    modules_total: int = 0
    flows_ready: int = 0
    flows_total: int = 0
    accessibility_ready: int = 0
    accessibility_total: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def readiness_ratio(self) -> float:
        total = self.modules_total + self.flows_total + self.accessibility_total
        ready = self.modules_ready + self.flows_ready + self.accessibility_ready
        return 1.0 if total == 0 else round(ready / total, 4)

    def to_dict(self) -> dict:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "modules_ready": self.modules_ready,
            "modules_total": self.modules_total,
            "flows_ready": self.flows_ready,
            "flows_total": self.flows_total,
            "accessibility_ready": self.accessibility_ready,
            "accessibility_total": self.accessibility_total,
            "readiness_ratio": self.readiness_ratio,
            "errors": list(self.errors),
        }
