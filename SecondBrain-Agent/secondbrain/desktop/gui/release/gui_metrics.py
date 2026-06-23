from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuiRc1Metrics:
    startup_ms: int = 0
    shutdown_ms: int = 0
    module_count: int = 0
    flow_count: int = 0
    error_count: int = 0

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.startup_ms < 0:
            issues.append("startup_ms must not be negative")
        if self.shutdown_ms < 0:
            issues.append("shutdown_ms must not be negative")
        if self.module_count < 0 or self.flow_count < 0 or self.error_count < 0:
            issues.append("counts must not be negative")
        return issues

    def to_dict(self) -> dict:
        return {
            "startup_ms": self.startup_ms,
            "shutdown_ms": self.shutdown_ms,
            "module_count": self.module_count,
            "flow_count": self.flow_count,
            "error_count": self.error_count,
        }
