from __future__ import annotations

from ..provider_profiles import ProviderProfile
from ..provider_registry import ProviderRegistry
from ..settings_models import SettingDefinition
from .secret_policy import SecretSanitizer
from .security_models import SecretPolicy, SanitizationResult


class SecureSettingsExporter:
    def __init__(self, policy: SecretPolicy | str = SecretPolicy.REDACT) -> None:
        self.sanitizer = SecretSanitizer(policy)

    def export_settings(self, values: dict, definitions: dict[str, SettingDefinition]) -> SanitizationResult:
        return self.sanitizer.sanitize_settings(values, definitions)

    def export_provider_profiles(self, profiles: list[ProviderProfile], registry: ProviderRegistry) -> dict:
        exported = []
        redacted: list[str] = []
        blocked: list[str] = []
        for profile in profiles:
            definition = registry.get(profile.kind, profile.provider)
            result = self.sanitizer.sanitize_provider_values(profile.values, definition)
            redacted.extend(f"{profile.profile_id}.{key}" for key in result.redacted_keys)
            blocked.extend(f"{profile.profile_id}.{key}" for key in result.blocked_keys)
            exported.append({
                "profile_id": profile.profile_id,
                "kind": profile.kind.value,
                "provider": profile.provider,
                "enabled": profile.enabled,
                "values": result.payload,
            })
        return {"profiles": exported, "redacted_keys": redacted, "blocked_keys": blocked}
