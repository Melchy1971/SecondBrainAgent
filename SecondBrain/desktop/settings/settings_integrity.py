from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .settings_registry import SettingsRegistry
from .settings_snapshot import VersionedSettingsSnapshot, settings_checksum
from .settings_validation import SettingsValidator


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class IntegrityReport:
    valid: bool
    issues: list[IntegrityIssue]

    @property
    def blocking(self) -> list[IntegrityIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]


class SettingsIntegrityChecker:
    def __init__(self, registry: SettingsRegistry, validator: SettingsValidator | None = None) -> None:
        self.registry = registry
        self.validator = validator or SettingsValidator()

    def check_settings(self, settings: dict[str, Any]) -> IntegrityReport:
        issues: list[IntegrityIssue] = []
        for definition in self.registry.all():
            if definition.required and definition.key not in settings:
                issues.append(IntegrityIssue("missing_required", f"Missing required setting: {definition.key}"))
                continue
            if definition.key in settings:
                for validation_issue in self.validator.validate_value(definition, settings.get(definition.key)):
                    issues.append(
                        IntegrityIssue(
                            validation_issue.code,
                            f"{definition.key}: {validation_issue.message}",
                            validation_issue.severity,
                        )
                    )
        return IntegrityReport(valid=not any(issue.severity == "error" for issue in issues), issues=issues)

    def check_snapshot(self, snapshot: VersionedSettingsSnapshot) -> IntegrityReport:
        issues = []
        expected = settings_checksum(snapshot.settings)
        if snapshot.checksum != expected:
            issues.append(IntegrityIssue("checksum_mismatch", "Snapshot checksum does not match settings payload"))
        settings_report = self.check_settings(snapshot.settings)
        issues.extend(settings_report.issues)
        return IntegrityReport(valid=not any(issue.severity == "error" for issue in issues), issues=issues)
