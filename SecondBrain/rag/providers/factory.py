"""Factory for RAG embedding providers.

Fail-closed: the factory never silently defaults to fake/deterministic
embeddings. A provider must be named explicitly, and dev-only providers
(deterministic/local) are blocked in a production context unless the caller
explicitly opts in via ``allow_dev_only`` or the environment flag.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from secondbrain.rag.providers.base import (
    EmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
)
from secondbrain.rag.providers.deterministic_provider import DeterministicEmbeddingProvider
from secondbrain.rag.providers.gemini_provider import GeminiEmbeddingProvider
from secondbrain.rag.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from secondbrain.rag.providers.openai_embedding_provider import OpenAIEmbeddingProvider

ALLOW_DEV_ONLY_ENV = "SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK"
_DEV_ONLY_KEYS = {"deterministic", "local", "offline", "hash"}


def _env_flag(name: str, env: Mapping[str, str] | None) -> bool:
    src = os.environ if env is None else env
    return str(src.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


class EmbeddingFactory:
    """Create embedding providers from config dictionaries or typed config."""

    @staticmethod
    def _explicit_provider(
        provider_name: str | None,
        settings: Mapping[str, Any] | EmbeddingProviderConfig | None,
    ) -> bool:
        if provider_name:
            return True
        if isinstance(settings, EmbeddingProviderConfig):
            return True
        if isinstance(settings, Mapping):
            return bool(settings.get("provider") or settings.get("name"))
        return False

    @staticmethod
    def _to_config(
        provider_name: str | None,
        settings: Mapping[str, Any] | EmbeddingProviderConfig | None,
    ) -> EmbeddingProviderConfig:
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
        *,
        production: bool = False,
        allow_dev_only: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> EmbeddingProvider:
        if not cls._explicit_provider(provider_name, settings):
            raise EmbeddingProviderError(
                "no embedding provider specified; refusing to default to fake/deterministic "
                "embeddings. Pass an explicit provider (openai, ollama, gemini) or, for "
                "development only, provider='deterministic'."
            )

        config = cls._to_config(provider_name, settings)
        key = config.provider.strip().lower().replace("-", "_")
        enforce = bool(config.extra.get("enforce_dimensions", False))

        if key in _DEV_ONLY_KEYS:
            dev_allowed = allow_dev_only or _env_flag(ALLOW_DEV_ONLY_ENV, env)
            if production and not dev_allowed:
                raise EmbeddingProviderError(
                    f"provider {config.provider!r} is DEV_ONLY (deterministic/local) and is "
                    "blocked in production. Configure a semantic provider (openai/ollama), or set "
                    f"allow_dev_only=True / {ALLOW_DEV_ONLY_ENV}=1 for development only."
                )
            return DeterministicEmbeddingProvider.from_config(config)
        if key == "ollama":
            return OllamaEmbeddingProvider(
                host=config.host or "http://localhost:11434",
                model=config.model or "nomic-embed-text",
                client=config.extra.get("client"),
                dimensions=config.dimensions,
                enforce_dimensions=enforce,
            )
        if key in {"openai", "openai_compatible"}:
            return OpenAIEmbeddingProvider(
                model=config.model or "text-embedding-3-small",
                client=config.extra.get("client"),
                dimensions=config.dimensions,
                enforce_dimensions=enforce,
            )
        if key == "gemini":
            return GeminiEmbeddingProvider.from_config(config)

        raise EmbeddingProviderError(f"unsupported embedding provider: {config.provider}")
