"""Embedding provider contracts for RAG runtime.

This module is deliberately dependency-free. Provider implementations may use
HTTP clients or SDKs, but the rest of the RAG pipeline only depends on this
small contract. Providers must raise on failure and must never silently return
fake/deterministic vectors in place of a real result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class EmbeddingProviderError(RuntimeError):
    """Raised when an embedding provider cannot complete a request.

    Providers must raise this (or a subclass) on failure. They must never
    silently return fake/deterministic vectors instead of a real result.
    """


class ProviderOfflineError(EmbeddingProviderError):
    """Raised when a networked provider is unreachable (offline / transient)."""


class DimensionMismatchError(EmbeddingProviderError):
    """Raised when produced vectors do not match the configured dimension contract."""


class ModelNotAllowedError(EmbeddingProviderError):
    """Raised when a requested model is not in the configured allow-list."""


@dataclass(frozen=True)
class ProviderHealthReport:
    """Result of a live provider health probe (never a fake substitution).

    ``status`` is ``PASS`` only when a real probe succeeded. ``production_ready``
    is ``False`` for dev-only providers even when the probe passes, so a
    production gate can block them without inspecting provider internals.
    """

    status: str
    provider: str
    model: str | None
    dimensions: int
    semantic: bool
    production_ready: bool
    dev_only: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider": self.provider,
            "model": self.model,
            "dimensions": self.dimensions,
            "semantic": self.semantic,
            "production_ready": self.production_ready,
            "dev_only": self.dev_only,
            "error": self.error,
        }


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    """Configuration used to construct embedding providers."""

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
    """Validate and normalize provider output to ``list[list[float]]``."""

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


def validate_dimensions(vectors: list[list[float]], expected: int) -> None:
    """Raise ``DimensionMismatchError`` if any vector deviates from ``expected``."""

    for index, vector in enumerate(vectors):
        if len(vector) != expected:
            raise DimensionMismatchError(
                f"embedding row {index}: expected dimension {expected}, got {len(vector)}"
            )


def validate_model(model: str | None, allowed: tuple[str, ...] | list[str]) -> None:
    """Raise ``ModelNotAllowedError`` if ``model`` is not in a non-empty allow-list."""

    if allowed and model not in tuple(allowed):
        raise ModelNotAllowedError(
            f"model {model!r} is not in the allowed set {tuple(allowed)!r}"
        )


def provider_index_identity(provider: Any) -> str:
    """Stable vector-index identity ``provider:model:dimensions``."""

    name = str(getattr(provider, "name", "unknown")).strip() or "unknown"
    model = str(getattr(provider, "model", None) or "default").strip() or "default"
    dimensions = int(getattr(provider, "dimensions", 0) or 0)
    return f"{name}:{model}:{dimensions}"


def reindex_required(current_identity: str, stored_identity: str | None) -> bool:
    """True when no identity is stored yet or the provider identity changed."""

    return stored_identity is None or current_identity != stored_identity
