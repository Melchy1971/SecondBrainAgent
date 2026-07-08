from __future__ import annotations

from .settings_models import SettingDefinition, SettingType, SettingValidationIssue


class SettingsValidator:
    def validate_value(self, definition: SettingDefinition, value: object) -> list[SettingValidationIssue]:
        issues: list[SettingValidationIssue] = []
        if definition.required and (value is None or value == ""):
            issues.append(SettingValidationIssue(definition.key, "required", "Setting is required"))
            return issues
        if value is None:
            return issues

        expected = definition.setting_type
        if expected in {SettingType.STRING, SettingType.SECRET_REF} and not isinstance(value, str):
            issues.append(SettingValidationIssue(definition.key, "type", "Expected string value"))
        elif expected == SettingType.BOOLEAN and not isinstance(value, bool):
            issues.append(SettingValidationIssue(definition.key, "type", "Expected boolean value"))
        elif expected == SettingType.INTEGER and not isinstance(value, int):
            issues.append(SettingValidationIssue(definition.key, "type", "Expected integer value"))
        elif expected == SettingType.FLOAT and not isinstance(value, (int, float)):
            issues.append(SettingValidationIssue(definition.key, "type", "Expected numeric value"))
        elif expected == SettingType.CHOICE and definition.choices and value not in definition.choices:
            issues.append(SettingValidationIssue(definition.key, "choice", "Value is not an allowed choice"))

        if isinstance(value, (int, float)):
            if definition.min_value is not None and value < definition.min_value:
                issues.append(SettingValidationIssue(definition.key, "min", "Value below minimum"))
            if definition.max_value is not None and value > definition.max_value:
                issues.append(SettingValidationIssue(definition.key, "max", "Value above maximum"))
        return issues
