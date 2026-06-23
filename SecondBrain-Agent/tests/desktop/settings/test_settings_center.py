from pathlib import Path

import pytest

from secondbrain.desktop.settings import (
    SettingCategory,
    SettingDefinition,
    SettingType,
    SettingsRegistry,
    SettingsService,
    SettingsStore,
    default_settings_registry,
)


def service(tmp_path: Path) -> SettingsService:
    return SettingsService(SettingsStore(tmp_path / "settings.json"))


def test_default_registry_contains_core_categories() -> None:
    registry = default_settings_registry()
    categories = registry.categories()
    assert "desktop" in categories
    assert "rag" in categories
    assert "connectors" in categories
    assert "security" in categories


def test_settings_service_loads_defaults(tmp_path: Path) -> None:
    settings = service(tmp_path)
    assert settings.get("desktop.theme") == "system"
    assert settings.get("rag.max_results") == 10


def test_settings_service_persists_update(tmp_path: Path) -> None:
    settings = service(tmp_path)
    settings.set("desktop.theme", "dark")

    reloaded = service(tmp_path)
    assert reloaded.get("desktop.theme") == "dark"


def test_invalid_choice_is_rejected(tmp_path: Path) -> None:
    settings = service(tmp_path)
    with pytest.raises(ValueError):
        settings.set("desktop.theme", "blue")


def test_numeric_bounds_are_enforced(tmp_path: Path) -> None:
    settings = service(tmp_path)
    with pytest.raises(ValueError):
        settings.set("rag.max_results", 0)


def test_secret_values_are_masked_in_snapshot(tmp_path: Path) -> None:
    settings = service(tmp_path)
    settings.set("security.vault_ref", "vault://openai")
    assert settings.snapshot().values["security.vault_ref"] == "***"
    assert settings.export(include_secrets=True)["security.vault_ref"] == "vault://openai"


def test_reset_restores_default(tmp_path: Path) -> None:
    settings = service(tmp_path)
    settings.set("desktop.theme", "dark")
    settings.reset("desktop.theme")
    assert settings.get("desktop.theme") == "system"


def test_registry_rejects_duplicate_keys() -> None:
    registry = SettingsRegistry()
    definition = SettingDefinition(
        key="x.y",
        category=SettingCategory.ADVANCED,
        setting_type=SettingType.STRING,
        default="",
        label="Y",
    )
    registry.register(definition)
    with pytest.raises(ValueError):
        registry.register(definition)
