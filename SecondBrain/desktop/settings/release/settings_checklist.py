from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


REQUIRED_SETTINGS_RC1_ITEMS = [
    "settings_foundation",
    "provider_profiles",
    "security_governance",
    "privacy_mode",
    "secret_handling",
    "backup_restore",
    "migration_support",
    "integrity_validation",
    "rollback_support",
]


@dataclass(frozen=True)
class SettingsChecklistItem:
    key: str
    status: str = "PASS"
    message: str = ""


@dataclass
class SettingsChecklist:
    items: list[SettingsChecklistItem] = field(default_factory=list)

    @classmethod
    def default(cls) -> "SettingsChecklist":
        return cls([SettingsChecklistItem(key) for key in REQUIRED_SETTINGS_RC1_ITEMS])

    @classmethod
    def from_keys(cls, passed_keys: Iterable[str]) -> "SettingsChecklist":
        passed = set(passed_keys)
        return cls([
            SettingsChecklistItem(
                key=key,
                status="PASS" if key in passed else "FAIL",
                message="available" if key in passed else "missing",
            )
            for key in REQUIRED_SETTINGS_RC1_ITEMS
        ])

    def status(self) -> str:
        if any(item.status == "FAIL" for item in self.items):
            return "FAIL"
        if any(item.status == "WARNING" for item in self.items):
            return "WARNING"
        return "PASS"

    def to_dict(self) -> dict:
        return {
            "status": self.status(),
            "items": [item.__dict__.copy() for item in self.items],
        }
