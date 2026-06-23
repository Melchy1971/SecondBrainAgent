from __future__ import annotations

from .settings_models import SettingCategory, SettingDefinition, SettingType


class SettingsRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, SettingDefinition] = {}

    def register(self, definition: SettingDefinition) -> None:
        if not definition.key:
            raise ValueError("setting key is required")
        if definition.key in self._definitions:
            raise ValueError(f"setting already registered: {definition.key}")
        self._definitions[definition.key] = definition

    def get(self, key: str) -> SettingDefinition:
        try:
            return self._definitions[key]
        except KeyError as exc:
            raise KeyError(f"unknown setting: {key}") from exc

    def all(self) -> list[SettingDefinition]:
        return list(self._definitions.values())

    def by_category(self, category: SettingCategory) -> list[SettingDefinition]:
        return [definition for definition in self._definitions.values() if definition.category == category]

    def categories(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for definition in self._definitions.values():
            result.setdefault(definition.category.value, []).append(definition.key)
        return {category: sorted(keys) for category, keys in result.items()}


def default_settings_registry() -> SettingsRegistry:
    registry = SettingsRegistry()
    registry.register(SettingDefinition(
        key="desktop.theme",
        category=SettingCategory.DESKTOP,
        setting_type=SettingType.CHOICE,
        default="system",
        label="Theme",
        choices=("system", "light", "dark"),
    ))
    registry.register(SettingDefinition(
        key="desktop.sidebar_collapsed",
        category=SettingCategory.DESKTOP,
        setting_type=SettingType.BOOLEAN,
        default=False,
        label="Sidebar collapsed",
    ))
    registry.register(SettingDefinition(
        key="rag.provider",
        category=SettingCategory.RAG,
        setting_type=SettingType.CHOICE,
        default="deterministic",
        label="Embedding provider",
        choices=("deterministic", "ollama", "openai", "gemini"),
    ))
    registry.register(SettingDefinition(
        key="rag.max_results",
        category=SettingCategory.RAG,
        setting_type=SettingType.INTEGER,
        default=10,
        label="Max search results",
        min_value=1,
        max_value=100,
    ))
    registry.register(SettingDefinition(
        key="connectors.sync_enabled",
        category=SettingCategory.CONNECTORS,
        setting_type=SettingType.BOOLEAN,
        default=True,
        label="Connector sync enabled",
    ))
    registry.register(SettingDefinition(
        key="security.vault_ref",
        category=SettingCategory.SECURITY,
        setting_type=SettingType.SECRET_REF,
        default="",
        label="Vault reference",
        secret=True,
    ))
    registry.register(SettingDefinition(
        key="general.default_workspace",
        category=SettingCategory.GENERAL,
        setting_type=SettingType.STRING,
        default="default",
        label="Default workspace",
        required=True,
    ))
    return registry
