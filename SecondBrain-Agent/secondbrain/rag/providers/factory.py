"""Factory for RAG embedding providers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from secondbrain.rag.providers.base import EmbeddingProvider, EmbeddingProviderConfig, EmbeddingProviderError
from secondbrain.rag.providers.deterministic_provider import DeterministicEmbeddingProvider
from secondbrain.rag.providers.gemini_provider import GeminiEmbeddingProvider
from secondbrain.rag.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from secondbrain.rag.providers.openai_embedding_provider import OpenAIEmbeddingProvider


class EmbeddingFactory:
    """Create embedding providers from config dictionaries or typed config."""

    @staticmethod
    def _to_config(provider_name: str | None, settings: Mapping[str, Any] | EmbeddingProviderConfig | None) -> EmbeddingProviderConfig:
        if isinstance(settings, EmbeddingProviderConfig):
            return settings if provider_name is None else EmbeddingProviderConfig(**{**settings.__dict__, "provider": provider_name})
        data = dict(settings or {})
        provider = provider_name or data.pop("provider", None) or data.pop("name", None) or "deterministic"
        known = {"model", "host", "api_key", "timeout_seconds", "dimensions"}
        extra = dict(data.pop("extra", {}))
        for key in list(data.keys()):
            if key not in known:
                extra[key] = data.pop(key)
        return EmbeddingProviderConfig(provider=str(provider), extra=extra, **data)

    @classmethod
    def create(
        cls,
        provider_name: str | None = None,
        settings: Mapping[str, Any] | EmbeddingProviderConfig | None = None,
    ) -> EmbeddingProvider:
        config = cls._to_config(provider_name, settings)
        key = config.provider.strip().lower().replace("-", "_")

        if key in {"deterministic", "local", "offline", "hash"}:
            return DeterministicEmbeddingProvider.from_config(config)
        if key == "ollama":
            return OllamaEmbeddingProvider(
                host=config.host or "http://localhost:11434",
                model=config.model or "nomic-embed-text",
                client=config.extra.get("client"),
            )
        if key in {"openai", "openai_compatible"}:
            return OpenAIEmbeddingProvider(
                model=config.model or "text-embedding-3-small",
                client=config.extra.get("client"),
            )
        if key == "gemini":
            return GeminiEmbeddingProvider.from_config(config)

        raise EmbeddingProviderError(f"unsupported embedding provider: {config.provider}")
