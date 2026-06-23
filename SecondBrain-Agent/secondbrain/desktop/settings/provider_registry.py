from __future__ import annotations

from .provider_profiles import ProviderDefinition, ProviderField, ProviderKind


class ProviderRegistry:
    def __init__(self) -> None:
        self._definitions: dict[tuple[ProviderKind, str], ProviderDefinition] = {}

    def register(self, definition: ProviderDefinition) -> None:
        key = (definition.kind, definition.provider)
        if key in self._definitions:
            raise ValueError(f"provider already registered: {definition.kind.value}.{definition.provider}")
        self._definitions[key] = definition

    def get(self, kind: ProviderKind | str, provider: str) -> ProviderDefinition:
        kind_value = ProviderKind(kind)
        try:
            return self._definitions[(kind_value, provider)]
        except KeyError as exc:
            raise KeyError(f"unknown provider: {kind_value.value}.{provider}") from exc

    def list(self, kind: ProviderKind | str | None = None) -> list[ProviderDefinition]:
        if kind is None:
            return list(self._definitions.values())
        kind_value = ProviderKind(kind)
        return [definition for definition in self._definitions.values() if definition.kind == kind_value]


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(ProviderDefinition(
        kind=ProviderKind.EMBEDDING,
        provider="deterministic",
        label="Deterministic local embeddings",
        fields=(ProviderField("dimension", "integer", default=384, min_value=8, max_value=4096),),
    ))
    registry.register(ProviderDefinition(
        kind=ProviderKind.EMBEDDING,
        provider="ollama",
        label="Ollama embeddings",
        fields=(
            ProviderField("base_url", "string", required=True, default="http://localhost:11434"),
            ProviderField("model", "string", required=True, default="nomic-embed-text"),
            ProviderField("timeout_seconds", "integer", default=30, min_value=1, max_value=300),
        ),
    ))
    registry.register(ProviderDefinition(
        kind=ProviderKind.LLM,
        provider="openai",
        label="OpenAI LLM",
        fields=(
            ProviderField("model", "string", required=True, default="gpt-4.1-mini"),
            ProviderField("api_key_ref", "secret_ref", required=True, secret=True),
            ProviderField("temperature", "float", default=0.2, min_value=0.0, max_value=2.0),
        ),
    ))
    registry.register(ProviderDefinition(
        kind=ProviderKind.OCR,
        provider="tesseract",
        label="Tesseract OCR",
        fields=(
            ProviderField("language", "string", default="deu+eng"),
            ProviderField("enabled", "boolean", default=False),
        ),
    ))
    registry.register(ProviderDefinition(
        kind=ProviderKind.STORAGE,
        provider="local",
        label="Local storage",
        fields=(
            ProviderField("root_path", "string", required=True, default=".secondbrain/storage"),
            ProviderField("max_mb", "integer", default=1024, min_value=1),
        ),
    ))
    registry.register(ProviderDefinition(
        kind=ProviderKind.CONNECTOR,
        provider="gmail",
        label="Gmail connector",
        fields=(
            ProviderField("account", "string", required=True),
            ProviderField("token_ref", "secret_ref", required=True, secret=True),
            ProviderField("sync_enabled", "boolean", default=False),
        ),
    ))
    return registry
