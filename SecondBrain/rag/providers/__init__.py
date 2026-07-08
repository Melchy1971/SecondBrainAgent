"""Embedding provider adapters used by the RAG pipeline."""

from secondbrain.rag.providers.base import (
    EmbeddingBatch,
    EmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
    EmbeddingResult,
    normalize_vectors,
)
from secondbrain.rag.providers.deterministic_provider import DeterministicEmbeddingProvider
from secondbrain.rag.providers.factory import EmbeddingFactory
from secondbrain.rag.providers.gemini_provider import GeminiEmbeddingProvider
from secondbrain.rag.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from secondbrain.rag.providers.openai_embedding_provider import OpenAIEmbeddingProvider

__all__ = [
    "DeterministicEmbeddingProvider",
    "EmbeddingBatch",
    "EmbeddingFactory",
    "EmbeddingProvider",
    "EmbeddingProviderConfig",
    "EmbeddingProviderError",
    "EmbeddingResult",
    "GeminiEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "normalize_vectors",
]
