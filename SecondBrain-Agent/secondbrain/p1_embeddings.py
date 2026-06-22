from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib import request


DEFAULT_DIMENSIONS = 64


class EmbeddingProvider(Protocol):
    name: str
    dimensions: int

    def embed(self, text: str) -> list[float]:
        ...

    def status(self) -> dict[str, Any]:
        ...


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 0:
        return vector
    return [round(v / norm, 8) for v in vector]


def deterministic_embedding(text: str, dimensions: int = DEFAULT_DIMENSIONS) -> list[float]:
    """Offline embedding fallback.

    Nicht semantisch, aber deterministisch und testbar. Dadurch kann der RAG-Core
    ohne Netzwerk/API-Key validiert werden; echte Provider ersetzen nur diese
    Projektionsfunktion, nicht die VectorStore-/Gate-Logik.
    """
    dims = max(8, int(dimensions))
    vec = [0.0] * dims
    for token in (text or "").lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for idx, byte in enumerate(digest):
            pos = (idx + digest[0]) % dims
            sign = 1.0 if byte % 2 == 0 else -1.0
            vec[pos] += sign * (1.0 + (byte % 13) / 13.0)
    return _normalize(vec)


@dataclass(frozen=True)
class LocalEmbeddingProvider:
    dimensions: int = DEFAULT_DIMENSIONS
    name: str = "local-deterministic"

    def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimensions)

    def status(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.name, "dimensions": self.dimensions, "network": False, "mode": "fallback"}


@dataclass(frozen=True)
class OllamaEmbeddingProvider:
    model: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"
    dimensions: int = DEFAULT_DIMENSIONS
    timeout_seconds: float = 2.0
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    name: str = "ollama"

    def embed(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = request.Request(f"{self.base_url.rstrip('/')}/api/embeddings", data=payload, headers={"Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec - local/user configured endpoint
                data = json.loads(response.read().decode("utf-8"))
            vector = data.get("embedding")
            if isinstance(vector, list) and vector:
                return _normalize([float(v) for v in vector])
        except Exception:
            pass
        return self.fallback.embed(text)

    def status(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.name, "model": self.model, "base_url": self.base_url, "dimensions": self.dimensions, "fallback": self.fallback.name, "network": True}


@dataclass(frozen=True)
class OpenAIEmbeddingProvider:
    model: str = "text-embedding-3-small"
    api_key_env: str = "OPENAI_API_KEY"
    dimensions: int = DEFAULT_DIMENSIONS
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    name: str = "openai"

    def embed(self, text: str) -> list[float]:
        # Offline-safe boundary: no dependency on external SDK and no network call in tests.
        # Runtime integration can replace this method with the official client while keeping
        # the same interface and VectorStore contract.
        return self.fallback.embed(text)

    def status(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.name, "model": self.model, "api_key_configured": bool(os.getenv(self.api_key_env)), "dimensions": self.dimensions, "fallback": self.fallback.name, "network": True}


def provider_from_profile(project_root: str | Path, profile: str | None = None) -> EmbeddingProvider:
    root = Path(project_root)
    config_path = root / "config" / "vector_rag.yaml"
    provider = os.getenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local").strip().lower()
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8", errors="ignore").lower()
        if "embedding_provider: ollama" in text or "provider: ollama" in text:
            provider = "ollama"
        elif "embedding_provider: openai" in text or "provider: openai" in text:
            provider = "openai"
    if provider == "ollama":
        return OllamaEmbeddingProvider()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    return LocalEmbeddingProvider()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    size = min(len(a), len(b))
    numerator = sum(a[i] * b[i] for i in range(size))
    da = math.sqrt(sum(a[i] * a[i] for i in range(size)))
    db = math.sqrt(sum(b[i] * b[i] for i in range(size)))
    if da <= 0 or db <= 0:
        return 0.0
    return numerator / (da * db)
