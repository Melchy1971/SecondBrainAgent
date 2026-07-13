from __future__ import annotations

from typing import Any

from ..provider_profiles import ProviderDefinition
from ..settings_models import SettingDefinition
from .security_models import SanitizationResult, SecretPolicy


class SecretSanitizer:
    def __init__(self, policy: SecretPolicy | str = SecretPolicy.REDACT) -> None:
        self.policy = SecretPolicy(policy)

    def sanitize_settings(self, values: dict[str, Any], definitions: dict[str, SettingDefinition]) -> SanitizationResult:
        payload = dict(values)
        redacted: list[str] = []
        blocked: list[str] = []
        for key, definition in definitions.items():
            if not definition.secret or key not in payload or payload[key] in (None, ""):
                continue
            self._apply(payload, key, redacted, blocked)
        return SanitizationResult(payload=payload, redacted_keys=tuple(redacted), blocked_keys=tuple(blocked))

    def sanitize_provider_values(self, values: dict[str, Any], definition: ProviderDefinition) -> SanitizationResult:
        payload = dict(values)
        redacted: list[str] = []
        blocked: list[str] = []
        for field in definition.fields:
            if not field.secret or field.key not in payload or payload[field.key] in (None, ""):
                continue
            self._apply(payload, field.key, redacted, blocked)
        return SanitizationResult(payload=payload, redacted_keys=tuple(redacted), blocked_keys=tuple(blocked))

    def _apply(self, payload: dict[str, Any], key: str, redacted: list[str], blocked: list[str]) -> None:
        if self.policy == SecretPolicy.REDACT:
            payload[key] = "***"
            redacted.append(key)
        elif self.policy == SecretPolicy.REFERENCE_ONLY:
            value = str(payload[key])
            payload[key] = value if value.startswith("secret://") else "secret://redacted"
            redacted.append(key)
        elif self.policy == SecretPolicy.BLOCK_EXPORT:
            payload.pop(key, None)
            blocked.append(key)
