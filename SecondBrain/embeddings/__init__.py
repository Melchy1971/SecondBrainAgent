"""Production embedding provider layer (v30.64).

Never silently substitutes fake embeddings; production gates FAIL on error.
"""
from secondbrain.embeddings.base import (
    EmbeddingConfig, ProviderHealth, EmbeddingProvider, EmbeddingProviderError,
    OfflineError, DimensionMismatchError, ModelNotAllowedError, provider_identity,
)
from secondbrain.embeddings.providers import (
    LocalEmbeddingProvider, OpenAIEmbeddingProvider, OllamaEmbeddingProvider,
)
from secondbrain.embeddings.cache import EmbeddingCache, CachingEmbeddingProvider
from secondbrain.embeddings.batch import embed_batch_chunked
from secondbrain.embeddings.validation import validate_dimensions, validate_model
from secondbrain.embeddings.offline import is_offline
from secondbrain.embeddings.factory import build_provider
from secondbrain.embeddings.gate import embedding_production_gate
from secondbrain.embeddings.reindex import reindex_needed, maybe_reindex

__all__ = [
    "EmbeddingConfig", "ProviderHealth", "EmbeddingProvider", "EmbeddingProviderError",
    "OfflineError", "DimensionMismatchError", "ModelNotAllowedError", "provider_identity",
    "LocalEmbeddingProvider", "OpenAIEmbeddingProvider", "OllamaEmbeddingProvider",
    "EmbeddingCache", "CachingEmbeddingProvider", "embed_batch_chunked",
    "validate_dimensions", "validate_model", "is_offline", "build_provider",
    "embedding_production_gate", "reindex_needed", "maybe_reindex",
]
