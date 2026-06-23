from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SettingsValidationIssue:
    code: str
    severity: str
    message: str


@dataclass
class SettingsValidationResult:
    status: str = "PASS"
    issues: list[SettingsValidationIssue] = field(default_factory=list)

    def add(self, code: str, severity: str, message: str) -> None:
        self.issues.append(SettingsValidationIssue(code, severity, message))
        if severity in {"FAIL", "BLOCKED"}:
            self.status = severity
        elif severity == "WARNING" and self.status == "PASS":
            self.status = "WARNING"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "issues": [issue.__dict__.copy() for issue in self.issues],
        }


class SettingsRC1Validator:
    def validate(self, settings_snapshot: dict | None = None) -> SettingsValidationResult:
        result = SettingsValidationResult()
        snapshot = settings_snapshot or {}
        if snapshot.get("privacy_mode") is False:
            result.add("PRIVACY_MODE_DISABLED", "WARNING", "privacy mode is explicitly disabled")
        if "secrets" in snapshot:
            result.add("RAW_SECRETS_IN_SETTINGS", "FAIL", "raw secrets must not be stored in settings")
        if snapshot.get("schema_version") in {None, ""}:
            result.add("MISSING_SCHEMA_VERSION", "WARNING", "settings schema version is missing")
        return result
