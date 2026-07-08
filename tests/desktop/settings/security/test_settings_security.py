from __future__ import annotations

import pytest

from secondbrain.desktop.settings import SettingCategory, SettingDefinition, SettingType
from secondbrain.desktop.settings.provider_profiles import ProviderField, ProviderKind, ProviderProfile
from secondbrain.desktop.settings.provider_registry import ProviderRegistry, default_provider_registry
from secondbrain.desktop.settings.security import (
    PrivacyMode,
    PrivacyModeService,
    SecretPolicy,
    SecretReference,
    SecretSanitizer,
    SettingsAuditAction,
    SettingsAuditLog,
    SecureSettingsExporter,
)


def test_secret_reference_requires_secret_scheme():
    assert SecretReference("secret://openai/api_key").public_value() == "secret://openai/api_key"
    with pytest.raises(ValueError):
        SecretReference("plain-token")


def test_privacy_mode_blocks_sensitive_operations():
    service = PrivacyModeService(PrivacyMode.STRICT)
    assert service.enabled() is True
    with pytest.raises(PermissionError):
        service.require_not_privacy_mode("memory_extract")
    service.set_mode(PrivacyMode.OFF)
    service.require_not_privacy_mode("memory_extract")


def test_secret_sanitizer_redacts_setting_secrets():
    definitions = {
        "api_key": SettingDefinition("api_key", SettingCategory.SECURITY, SettingType.SECRET_REF, "", "API", secret=True),
        "theme": SettingDefinition("theme", SettingCategory.DESKTOP, SettingType.STRING, "dark", "Theme"),
    }
    result = SecretSanitizer().sanitize_settings({"api_key": "secret-value", "theme": "dark"}, definitions)
    assert result.payload["api_key"] == "***"
    assert result.payload["theme"] == "dark"
    assert result.redacted_keys == ("api_key",)


def test_secret_sanitizer_blocks_exported_secret_values():
    definitions = {
        "api_key": SettingDefinition("api_key", SettingCategory.SECURITY, SettingType.SECRET_REF, "", "API", secret=True),
    }
    result = SecretSanitizer(SecretPolicy.BLOCK_EXPORT).sanitize_settings({"api_key": "secret-value"}, definitions)
    assert "api_key" not in result.payload
    assert result.blocked_keys == ("api_key",)


def test_secret_sanitizer_converts_plain_secret_to_reference_only():
    definition = default_provider_registry().get(ProviderKind.LLM, "openai")
    result = SecretSanitizer(SecretPolicy.REFERENCE_ONLY).sanitize_provider_values({"api_key_ref": "plain", "model": "x"}, definition)
    assert result.payload["api_key_ref"] == "secret://redacted"
    assert result.payload["model"] == "x"


def test_settings_audit_log_records_change():
    audit = SettingsAuditLog()
    entry = audit.record(SettingsAuditAction.UPDATED, "rag.top_k", before=5, after=10, actor="tester")
    assert entry.key == "rag.top_k"
    assert audit.by_key("rag.top_k")[0].after == 10
    assert audit.export()[0]["action"] == "updated"


def test_secure_provider_export_redacts_secret_fields():
    registry = default_provider_registry()
    profile = ProviderProfile(
        profile_id="emb-openai",
        kind=ProviderKind.LLM,
        provider="openai",
        values={"api_key_ref": "raw-secret", "model": "gpt-4.1-mini"},
    )
    payload = SecureSettingsExporter().export_provider_profiles([profile], registry)
    assert payload["profiles"][0]["values"]["api_key_ref"] == "***"
    assert "emb-openai.api_key_ref" in payload["redacted_keys"]


def test_secure_settings_exporter_preserves_non_secret_values():
    definitions = {
        "privacy_mode": SettingDefinition("privacy_mode", SettingCategory.SECURITY, SettingType.CHOICE, "off", "Privacy", choices=("off", "strict")),
    }
    result = SecureSettingsExporter().export_settings({"privacy_mode": "strict"}, definitions)
    assert result.payload == {"privacy_mode": "strict"}
    assert result.redacted_keys == ()
