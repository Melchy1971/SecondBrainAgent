"""Embedding provider contracts for RAG runtime.

This module is deliberately dependency-free. Provider implementations may use
HTTP clients, SDKs, or deterministic local fallbacks, but the rest of the RAG
pipeline only depends on this small contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class EmbeddingProviderError(RuntimeError):
    """Raised when an embedding provider cannot complete a request."""


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    """Configuration used to construct embedding providers.

    Attributes:
        provider: Provider key, for example ``ollama``, ``openai``, ``gemini``
            or ``deterministic``.
        model: Provider model name.
        host: Optional base URL for local or OpenAI-compatible providers.
        api_key: Optional API key. If omitted, provider implementations may read
            their standard environment variables.
        timeout_seconds: Network timeout passed to provider HTTP clients.
        dimensions: Optional output vector size for deterministic/local providers.
        extra: Provider-specific extension values.
    """

    provider: str = "deterministic"
    model: str | None = None
    host: str | None = None
    api_key: str | None = None
    timeout_seconds: float = 60.0
    dimensions: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingBatch:
    """Embedding request payload."""

    texts: list[str]
    model: str | None = None


@dataclass(frozen=True)
class EmbeddingResult:
    """Normalized embedding provider response."""

    vectors: list[list[float]]
    provider: str
    model: str | None
    dimensions: int


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Minimal contract consumed by indexing and retrieval code."""

    name: str
    model: str | None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""

    def embed_batch(self, batch: EmbeddingBatch) -> EmbeddingResult:
        """Return normalized metadata with the generated vectors."""
        vectors = self.embed(batch.texts)
        dimensions = len(vectors[0]) if vectors else 0
        return EmbeddingResult(
            vectors=vectors,
            provider=self.name,
            model=batch.model or self.model,
            dimensions=dimensions,
        )


def normalize_vectors(vectors: list[list[float]], expected_count: int) -> list[list[float]]:
    """Validate and normalize provider output to ``list[list[float]]``.

    The function protects downstream vector stores from SDK-specific types,
    strings, integers, malformed rows, and row-count mismatches.
    """

    if len(vectors) != expected_count:
        raise EmbeddingProviderError(
            f"embedding count mismatch: expected {expected_count}, got {len(vectors)}"
        )

    normalized: list[list[float]] = []
    dimensions: int | None = None
    for index, row in enumerate(vectors):
        if not isinstance(row, list) or not row:
            raise EmbeddingProviderError(f"embedding row {index} is empty or invalid")
        try:
            converted = [float(value) for value in row]
        except (TypeError, ValueError) as exc:
            raise EmbeddingProviderError(f"embedding row {index} contains non-numeric values") from exc
        if dimensions is None:
            dimensions = len(converted)
        elif len(converted) != dimensions:
            raise EmbeddingProviderError(
                f"embedding row {index} has dimension {len(converted)}; expected {dimensions}"
            )
        normalized.append(converted)
    return normalized
