from __future__ import annotations

from .provider_profiles import ProviderDefinition, ProviderProfile, ProviderValidationIssue


class ProviderProfileValidator:
    def validate(self, definition: ProviderDefinition, profile: ProviderProfile) -> list[ProviderValidationIssue]:
        issues: list[ProviderValidationIssue] = []
        if profile.kind != definition.kind:
            issues.append(ProviderValidationIssue(profile.profile_id, "kind", "kind_mismatch", "Profile kind does not match provider definition"))
        if profile.provider != definition.provider:
            issues.append(ProviderValidationIssue(profile.profile_id, "provider", "provider_mismatch", "Profile provider does not match definition"))

        fields = {field.key: field for field in definition.fields}
        for field in definition.fields:
            value = profile.values.get(field.key, field.default)
            if field.required and (value is None or value == ""):
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "required", "Field is required"))
                continue
            if value is None:
                continue
            if field.field_type in {"string", "secret_ref"} and not isinstance(value, str):
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "type", "Expected string value"))
            elif field.field_type == "boolean" and not isinstance(value, bool):
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "type", "Expected boolean value"))
            elif field.field_type == "integer" and not isinstance(value, int):
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "type", "Expected integer value"))
            elif field.field_type == "float" and not isinstance(value, (int, float)):
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "type", "Expected numeric value"))
            elif field.field_type == "choice" and field.choices and value not in field.choices:
                issues.append(ProviderValidationIssue(profile.profile_id, field.key, "choice", "Value is not allowed"))

            if isinstance(value, (int, float)):
                if field.min_value is not None and value < field.min_value:
                    issues.append(ProviderValidationIssue(profile.profile_id, field.key, "min", "Value below minimum"))
                if field.max_value is not None and value > field.max_value:
                    issues.append(ProviderValidationIssue(profile.profile_id, field.key, "max", "Value above maximum"))

        for key in profile.values:
            if key not in fields:
                issues.append(ProviderValidationIssue(profile.profile_id, key, "unknown", "Unknown provider field", severity="warning"))
        return issues
