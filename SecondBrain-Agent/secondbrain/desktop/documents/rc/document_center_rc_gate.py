from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class GateStatus(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    FAIL = "FAIL"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


@dataclass(frozen=True)
class GateFinding:
    code: str
    severity: FindingSeverity
    message: str
    component: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "component": self.component,
        }


@dataclass(frozen=True)
class DocumentCenterCapability:
    name: str
    implemented: bool
    tested: bool
    user_safe: bool = True
    notes: str = ""

    def is_ready(self) -> bool:
        return self.implemented and self.tested and self.user_safe

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "implemented": self.implemented,
            "tested": self.tested,
            "user_safe": self.user_safe,
            "ready": self.is_ready(),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class DocumentCenterGateResult:
    status: GateStatus
    checked_at: str
    capabilities: list[DocumentCenterCapability]
    findings: list[GateFinding] = field(default_factory=list)

    @property
    def ready_count(self) -> int:
        return sum(1 for capability in self.capabilities if capability.is_ready())

    @property
    def total_count(self) -> int:
        return len(self.capabilities)

    @property
    def readiness_ratio(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.ready_count / self.total_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checked_at": self.checked_at,
            "ready_count": self.ready_count,
            "total_count": self.total_count,
            "readiness_ratio": round(self.readiness_ratio, 4),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "findings": [finding.to_dict() for finding in self.findings],
        }


REQUIRED_CAPABILITIES = (
    "repository",
    "filters",
    "selection",
    "actions",
    "detail_view",
    "preview",
    "bulk_workflows",
    "persistence",
)


class DocumentCenterRCGate:
    def __init__(self, required_capabilities: tuple[str, ...] = REQUIRED_CAPABILITIES) -> None:
        self.required_capabilities = required_capabilities

    def evaluate(self, capability_state: Mapping[str, Mapping[str, Any]]) -> DocumentCenterGateResult:
        capabilities: list[DocumentCenterCapability] = []
        findings: list[GateFinding] = []

        for name in self.required_capabilities:
            raw = capability_state.get(name, {})
            capability = DocumentCenterCapability(
                name=name,
                implemented=bool(raw.get("implemented", False)),
                tested=bool(raw.get("tested", False)),
                user_safe=bool(raw.get("user_safe", True)),
                notes=str(raw.get("notes", "")),
            )
            capabilities.append(capability)
            findings.extend(self._findings_for(capability))

        status = self._derive_status(findings)
        return DocumentCenterGateResult(
            status=status,
            checked_at=datetime.now(timezone.utc).isoformat(),
            capabilities=capabilities,
            findings=findings,
        )

    def _findings_for(self, capability: DocumentCenterCapability) -> list[GateFinding]:
        findings: list[GateFinding] = []
        if not capability.implemented:
            findings.append(
                GateFinding(
                    code="DOCUMENT_CENTER_CAPABILITY_MISSING",
                    severity=FindingSeverity.BLOCKER,
                    component=capability.name,
                    message=f"Required document-center capability '{capability.name}' is not implemented.",
                )
            )
        if capability.implemented and not capability.tested:
            findings.append(
                GateFinding(
                    code="DOCUMENT_CENTER_TEST_COVERAGE_MISSING",
                    severity=FindingSeverity.WARNING,
                    component=capability.name,
                    message=f"Capability '{capability.name}' is implemented but not covered by tests.",
                )
            )
        if capability.implemented and capability.tested and not capability.user_safe:
            findings.append(
                GateFinding(
                    code="DOCUMENT_CENTER_USER_SAFETY_RISK",
                    severity=FindingSeverity.BLOCKER,
                    component=capability.name,
                    message=f"Capability '{capability.name}' exposes unsafe user-facing behavior.",
                )
            )
        return findings

    def _derive_status(self, findings: list[GateFinding]) -> GateStatus:
        if any(finding.severity == FindingSeverity.BLOCKER for finding in findings):
            return GateStatus.FAIL
        if any(finding.severity == FindingSeverity.WARNING for finding in findings):
            return GateStatus.CONDITIONAL_PASS
        return GateStatus.PASS


def default_rc1_capability_state() -> dict[str, dict[str, Any]]:
    return {
        "repository": {"implemented": True, "tested": True},
        "filters": {"implemented": True, "tested": True},
        "selection": {"implemented": True, "tested": True},
        "actions": {"implemented": True, "tested": True},
        "detail_view": {"implemented": True, "tested": True, "user_safe": True},
        "preview": {"implemented": True, "tested": True, "user_safe": True},
        "bulk_workflows": {"implemented": True, "tested": True, "user_safe": True},
        "persistence": {"implemented": True, "tested": True},
    }
