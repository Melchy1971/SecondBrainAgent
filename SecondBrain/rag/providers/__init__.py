"""Embedding provider adapters used by the RAG pipeline."""

from secondbrain.rag.providers.base import (
    DimensionMismatchError,
    EmbeddingBatch,
    EmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
    EmbeddingResult,
    ModelNotAllowedError,
    ProviderHealthReport,
    ProviderOfflineError,
    normalize_vectors,
    provider_index_identity,
    reindex_required,
    validate_dimensions,
    validate_model,
)
from secondbrain.rag.providers.deterministic_provider import DeterministicEmbeddingProvider
from secondbrain.rag.providers.factory import EmbeddingFactory
from secondbrain.rag.providers.gemini_provider import GeminiEmbeddingProvider
from secondbrain.rag.providers.health import embedding_production_gate, provider_health
from secondbrain.rag.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from secondbrain.rag.providers.openai_embedding_provider import OpenAIEmbeddingProvider

__all__ = [
    "DeterministicEmbeddingProvider",
    "DimensionMismatchError",
    "EmbeddingBatch",
    "EmbeddingFactory",
    "EmbeddingProvider",
    "EmbeddingProviderConfig",
    "EmbeddingProviderError",
    "EmbeddingResult",
    "GeminiEmbeddingProvider",
    "ModelNotAllowedError",
    "OllamaEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "ProviderHealthReport",
    "ProviderOfflineError",
    "embedding_production_gate",
    "normalize_vectors",
    "provider_health",
    "provider_index_identity",
    "reindex_required",
    "validate_dimensions",
    "validate_model",
]
