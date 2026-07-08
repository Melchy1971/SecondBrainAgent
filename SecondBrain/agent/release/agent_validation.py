from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class AgentValidationItem:
    key: str
    status: str
    message: str = ""
    severity: str = "INFO"

    @property
    def blocking(self) -> bool:
        return self.status in {"FAIL", "BLOCKED"} or self.severity == "CRITICAL"


@dataclass
class AgentValidation:
    """Validates whether all Agent RC1 capabilities are present and safe to expose."""

    required_capabilities: tuple[str, ...] = (
        "agent_foundation",
        "memory_context",
        "planning_execution",
        "tool_calling",
        "background_jobs",
        "approval_gates",
        "privacy_gates",
        "audit_trail",
    )

    def validate(self, capabilities: Mapping[str, bool]) -> list[AgentValidationItem]:
        results: list[AgentValidationItem] = []
        for capability in self.required_capabilities:
            enabled = bool(capabilities.get(capability, False))
            results.append(
                AgentValidationItem(
                    key=capability,
                    status="PASS" if enabled else "BLOCKED",
                    message="available" if enabled else "missing capability",
                    severity="INFO" if enabled else "CRITICAL",
                )
            )
        return results

    def status(self, capabilities: Mapping[str, bool]) -> str:
        items = self.validate(capabilities)
        if any(item.status == "BLOCKED" for item in items):
            return "BLOCKED"
        if any(item.status == "FAIL" for item in items):
            return "FAIL"
        return "PASS"
