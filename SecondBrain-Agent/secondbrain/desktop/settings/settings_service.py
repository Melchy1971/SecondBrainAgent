from __future__ import annotations

from typing import Any

from .settings_models import SettingsSnapshot, SettingValidationIssue
from .settings_registry import SettingsRegistry, default_settings_registry
from .settings_store import SettingsStore
from .settings_validation import SettingsValidator


class SettingsService:
    def __init__(
        self,
        store: SettingsStore,
        registry: SettingsRegistry | None = None,
        validator: SettingsValidator | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or default_settings_registry()
        self.validator = validator or SettingsValidator()
        self._values: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        persisted = self.store.load()
        defaults = {definition.key: definition.default for definition in self.registry.all()}
        defaults.update(persisted)
        self._values = defaults

    def get(self, key: str) -> Any:
        self.registry.get(key)
        return self._values.get(key)

    def set(self, key: str, value: Any) -> None:
        definition = self.registry.get(key)
        issues = self.validator.validate_value(definition, value)
        blocking = [issue for issue in issues if issue.severity == "error"]
        if blocking:
            joined = "; ".join(f"{issue.code}: {issue.message}" for issue in blocking)
            raise ValueError(joined)
        self._values[key] = value
        self.store.save(self.export(include_secrets=True))

    def reset(self, key: str) -> None:
        definition = self.registry.get(key)
        self._values[key] = definition.default
        self.store.save(self.export(include_secrets=True))

    def validate_all(self) -> list[SettingValidationIssue]:
        issues: list[SettingValidationIssue] = []
        for definition in self.registry.all():
            issues.extend(self.validator.validate_value(definition, self._values.get(definition.key)))
        return issues

    def export(self, include_secrets: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for definition in self.registry.all():
            value = self._values.get(definition.key)
            if definition.secret and not include_secrets:
                result[definition.key] = "***" if value else ""
            else:
                result[definition.key] = value
        return result

    def snapshot(self) -> SettingsSnapshot:
        return SettingsSnapshot(
            values=self.export(include_secrets=False),
            categories=self.registry.categories(),
            issues=self.validate_all(),
        )
