from __future__ import annotations

from .provider_profiles import ProviderKind, ProviderProfile, ProviderValidationIssue
from .provider_registry import ProviderRegistry, default_provider_registry
from .provider_store import ProviderProfileStore
from .provider_validation import ProviderProfileValidator


class ProviderProfileService:
    def __init__(
        self,
        store: ProviderProfileStore,
        registry: ProviderRegistry | None = None,
        validator: ProviderProfileValidator | None = None,
    ) -> None:
        self.store = store
        self.registry = registry or default_provider_registry()
        self.validator = validator or ProviderProfileValidator()
        self._profiles: dict[str, ProviderProfile] = {profile.profile_id: profile for profile in self.store.load()}

    def create_profile(self, profile_id: str, kind: ProviderKind | str, provider: str, values: dict | None = None, enabled: bool = True) -> ProviderProfile:
        if profile_id in self._profiles:
            raise ValueError(f"provider profile already exists: {profile_id}")
        definition = self.registry.get(kind, provider)
        merged = definition.defaults()
        merged.update(values or {})
        profile = ProviderProfile(profile_id=profile_id, kind=definition.kind, provider=provider, enabled=enabled, values=merged)
        self._raise_on_errors(profile)
        self._profiles[profile_id] = profile
        self._persist()
        return profile.copy()

    def get_profile(self, profile_id: str, redact_secrets: bool = True) -> ProviderProfile:
        profile = self._profiles[profile_id].copy()
        if redact_secrets:
            self._redact(profile)
        return profile

    def list_profiles(self, kind: ProviderKind | str | None = None, redact_secrets: bool = True) -> list[ProviderProfile]:
        profiles = [profile.copy() for profile in self._profiles.values()]
        if kind is not None:
            kind_value = ProviderKind(kind)
            profiles = [profile for profile in profiles if profile.kind == kind_value]
        if redact_secrets:
            for profile in profiles:
                self._redact(profile)
        return sorted(profiles, key=lambda profile: profile.profile_id)

    def update_profile(self, profile_id: str, values: dict) -> ProviderProfile:
        profile = self._profiles[profile_id].copy()
        profile.values.update(values)
        self._raise_on_errors(profile)
        self._profiles[profile_id] = profile
        self._persist()
        return self.get_profile(profile_id)

    def set_enabled(self, profile_id: str, enabled: bool) -> ProviderProfile:
        profile = self._profiles[profile_id].copy()
        profile.enabled = enabled
        self._profiles[profile_id] = profile
        self._persist()
        return self.get_profile(profile_id)

    def delete_profile(self, profile_id: str) -> None:
        del self._profiles[profile_id]
        self._persist()

    def validate_profile(self, profile_id: str) -> list[ProviderValidationIssue]:
        profile = self._profiles[profile_id]
        definition = self.registry.get(profile.kind, profile.provider)
        return self.validator.validate(definition, profile)

    def export_profiles(self, include_secrets: bool = False) -> dict:
        profiles = []
        for profile in self.list_profiles(redact_secrets=not include_secrets):
            profiles.append({
                "profile_id": profile.profile_id,
                "kind": profile.kind.value,
                "provider": profile.provider,
                "enabled": profile.enabled,
                "values": profile.values,
            })
        return {"profiles": profiles}

    def import_profiles(self, payload: dict, replace: bool = False) -> None:
        incoming: dict[str, ProviderProfile] = {}
        for item in payload.get("profiles", []):
            definition = self.registry.get(item["kind"], item["provider"])
            profile = ProviderProfile(
                profile_id=item["profile_id"],
                kind=definition.kind,
                provider=definition.provider,
                enabled=bool(item.get("enabled", True)),
                values=dict(item.get("values", {})),
            )
            self._raise_on_errors(profile)
            incoming[profile.profile_id] = profile
        if replace:
            self._profiles = incoming
        else:
            self._profiles.update(incoming)
        self._persist()

    def _raise_on_errors(self, profile: ProviderProfile) -> None:
        definition = self.registry.get(profile.kind, profile.provider)
        issues = self.validator.validate(definition, profile)
        errors = [issue for issue in issues if issue.severity == "error"]
        if errors:
            raise ValueError("; ".join(f"{issue.key}:{issue.code}" for issue in errors))

    def _redact(self, profile: ProviderProfile) -> None:
        definition = self.registry.get(profile.kind, profile.provider)
        for field in definition.fields:
            if field.secret and profile.values.get(field.key):
                profile.values[field.key] = "***"

    def _persist(self) -> None:
        self.store.save(list(self._profiles.values()))
