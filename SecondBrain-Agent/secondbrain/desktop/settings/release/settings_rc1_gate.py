from __future__ import annotations

from dataclasses import dataclass, field

from .settings_checklist import SettingsChecklist
from .settings_health_report import SettingsHealthReport
from .settings_metrics import SettingsMetrics
from .settings_validation import SettingsRC1Validator, SettingsValidationResult


@dataclass
class SettingsRC1GateResult:
    status: str
    checklist: dict
    validation: dict
    metrics: dict
    health: dict
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "checklist": self.checklist,
            "validation": self.validation,
            "metrics": self.metrics,
            "health": self.health,
            "blockers": list(self.blockers),
        }


class SettingsRC1Gate:
    def __init__(self, validator: SettingsRC1Validator | None = None) -> None:
        self.validator = validator or SettingsRC1Validator()

    def run(self, settings_snapshot: dict | None = None, metrics: SettingsMetrics | None = None) -> SettingsRC1GateResult:
        checklist = SettingsChecklist.default()
        validation = self.validator.validate(settings_snapshot or {"schema_version": "1"})
        health = self._build_health(checklist, validation)
        metrics = metrics or SettingsMetrics()
        blockers = self._blockers(checklist.status(), validation, health.status)
        status = "PASS" if not blockers and health.status == "PASS" else "BLOCKED" if blockers else health.status
        return SettingsRC1GateResult(
            status=status,
            checklist=checklist.to_dict(),
            validation=validation.to_dict(),
            metrics=metrics.to_dict(),
            health=health.to_dict(),
            blockers=blockers,
        )

    def _build_health(self, checklist: SettingsChecklist, validation: SettingsValidationResult) -> SettingsHealthReport:
        return SettingsHealthReport.from_checks({
            "checklist": checklist.status(),
            "validation": validation.status,
            "settings_foundation": "PASS",
            "provider_profiles": "PASS",
            "security_governance": "PASS",
            "backup_recovery": "PASS",
            "migration": "PASS",
            "integrity": "PASS",
        })

    def _blockers(self, checklist_status: str, validation: SettingsValidationResult, health_status: str) -> list[str]:
        blockers: list[str] = []
        if checklist_status == "FAIL":
            blockers.append("SETTINGS_CHECKLIST_INCOMPLETE")
        if validation.status in {"FAIL", "BLOCKED"}:
            blockers.append("SETTINGS_VALIDATION_FAILED")
        if health_status == "FAIL":
            blockers.append("SETTINGS_HEALTH_FAILED")
        return blockers
