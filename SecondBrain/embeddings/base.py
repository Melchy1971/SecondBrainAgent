"""Embedding provider contract + errors (v30.64). Never silently substitutes fakes."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class EmbeddingProviderError(RuntimeError):
    """Base error for embedding providers. Callers must handle, never fall back to fakes silently."""


class OfflineError(EmbeddingProviderError):
    """Raised when a networked provider is unreachable (offline detection)."""


class DimensionMismatchError(EmbeddingProviderError):
    pass


class ModelNotAllowedError(EmbeddingProviderError):
    pass


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    model: str
    dimensions: int
    base_url: str = ""
    api_key_env: str = ""
    timeout_seconds: float = 10.0
    enforce_dimensions: bool = True
    allowed_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderHealth:
    status: str                 # "PASS" | "FAIL"
    provider: str
    model: str
    dimensions: int
    semantic: bool
    production_ready: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "provider": self.provider, "model": self.model,
                "dimensions": self.dimensions, "semantic": self.semantic,
                "production_ready": self.production_ready, "error": self.error}


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    model: str
    dimensions: int
    semantic: bool
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    def health(self) -> ProviderHealth: ...


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 0:
        return list(vector)
    return [round(v / norm, 8) for v in vector]


def provider_identity(provider: EmbeddingProvider) -> str:
    """Stable index identity: provider:model:dimensions (guards silent model swaps)."""
    return f"{getattr(provider, 'name', 'unknown')}:{getattr(provider, 'model', 'default')}:{int(getattr(provider, 'dimensions', 0))}"


def content_key(provider: str, model: str, dimensions: int, text: str) -> str:
    blob = f"{provider}\x1f{model}\x1f{dimensions}\x1f{text}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
