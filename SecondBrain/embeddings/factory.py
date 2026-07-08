"""Provider factory. NEVER silently substitutes a fake/local provider."""

from __future__ import annotations

import os

from secondbrain.embeddings.base import EmbeddingConfig, EmbeddingProviderError
from secondbrain.embeddings.providers import (
    OpenAIEmbeddingProvider, OllamaEmbeddingProvider, LocalEmbeddingProvider,
)

ALLOW_LOCAL_ENV = "SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK"


def build_provider(config: EmbeddingConfig, *, allow_local: bool = False,
                   transport=None, env: dict | None = None):
    src = os.environ if env is None else env
    provider = config.provider.lower()

    if provider == "openai":
        return OpenAIEmbeddingProvider(model=config.model, dimensions=config.dimensions,
                                       api_key_env=config.api_key_env or "OPENAI_API_KEY",
                                       base_url=config.base_url or "https://api.openai.com",
                                       transport=transport, enforce_dimensions=config.enforce_dimensions,
                                       timeout_seconds=config.timeout_seconds)
    if provider == "ollama":
        return OllamaEmbeddingProvider(model=config.model, dimensions=config.dimensions,
                                       base_url=config.base_url or "http://localhost:11434",
                                       transport=transport, enforce_dimensions=config.enforce_dimensions,
                                       timeout_seconds=config.timeout_seconds)
    if provider == "local":
        allowed = allow_local or str(src.get(ALLOW_LOCAL_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}
        if not allowed:
            raise EmbeddingProviderError(
                "local (deterministic) embeddings requested but not explicitly allowed; "
                "refusing to serve fake embeddings. Set allow_local=True or "
                f"{ALLOW_LOCAL_ENV}=1 for development only.")
        return LocalEmbeddingProvider(dimensions=config.dimensions)

    raise EmbeddingProviderError(f"unknown embedding provider: {config.provider!r}")
