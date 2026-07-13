"""Embedding providers: Local (deterministic dev), OpenAI, Ollama.

Networked providers use an injectable Transport (offline-testable). They NEVER
return fake vectors on failure - they raise. Fakes exist only as an explicit
LocalEmbeddingProvider that reports production_ready=False.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

from secondbrain.connectors.scaffold.transport import Transport, UrllibTransport
from secondbrain.embeddings.base import (
    EmbeddingProviderError, OfflineError, DimensionMismatchError,
    ProviderHealth, normalize,
)

DEFAULT_DIMENSIONS = 64


def deterministic_embedding(text: str, dimensions: int) -> list[float]:
    dims = max(8, int(dimensions))
    vec = [0.0] * dims
    for token in (text or "").lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for idx, byte in enumerate(digest):
            pos = (idx + digest[0]) % dims
            vec[pos] += (1.0 if byte % 2 == 0 else -1.0) * (1.0 + (byte % 13) / 13.0)
    return normalize(vec)


@dataclass
class LocalEmbeddingProvider:
    """Deterministic, non-semantic. Development/tests only. Never production."""
    dimensions: int = DEFAULT_DIMENSIONS
    model: str = "local-deterministic"
    name: str = "local"
    semantic: bool = False

    def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text, self.dimensions)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    def health(self) -> ProviderHealth:
        return ProviderHealth("PASS", self.name, self.model, self.dimensions,
                              semantic=False, production_ready=False,
                              error="local deterministic embeddings are not production-ready")


class OpenAIEmbeddingProvider:
    name = "openai"
    semantic = True

    def __init__(self, *, model: str = "text-embedding-3-small", dimensions: int = 1536,
                 api_key: str | None = None, api_key_env: str = "OPENAI_API_KEY",
                 base_url: str = "https://api.openai.com", transport: Transport | None = None,
                 enforce_dimensions: bool = True, timeout_seconds: float = 10.0) -> None:
        self.model = model
        self.dimensions = dimensions
        self._api_key = api_key
        self.api_key_env = api_key_env
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrllibTransport(timeout=timeout_seconds)
        self.enforce_dimensions = enforce_dimensions

    def _key(self) -> str:
        key = self._api_key or os.getenv(self.api_key_env, "").strip()
        if not key:
            raise EmbeddingProviderError("openai_api_key_missing")  # never fall back to fake
        return key

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        try:
            resp = self.transport.request(
                "POST", f"{self.base_url}/v1/embeddings",
                headers={"Authorization": f"Bearer {self._key()}", "Content-Type": "application/json"},
                body=body)
        except EmbeddingProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - network boundary
            raise OfflineError(f"openai_unreachable: {exc}") from exc
        if resp.status == 401:
            raise EmbeddingProviderError("openai_unauthorized")
        if resp.status >= 500 or resp.status == 429:
            raise OfflineError(f"openai_transient_{resp.status}")
        if resp.status >= 400:
            raise EmbeddingProviderError(f"openai_error_{resp.status}")
        data = resp.json()
        vectors = [item["embedding"] for item in data.get("data", [])]
        if len(vectors) != len(texts):
            raise EmbeddingProviderError("openai_incomplete_batch")
        if self.enforce_dimensions:
            for v in vectors:
                if len(v) != self.dimensions:
                    raise DimensionMismatchError(f"openai_dim:expected={self.dimensions}:actual={len(v)}")
        return vectors

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def health(self) -> ProviderHealth:
        try:
            v = self.embed_batch(["secondbrain health probe"])[0]
            return ProviderHealth("PASS", self.name, self.model, len(v), True, True)
        except Exception as exc:  # noqa: BLE001
            return ProviderHealth("FAIL", self.name, self.model, self.dimensions, True, False, str(exc))


class OllamaEmbeddingProvider:
    name = "ollama"
    semantic = True

    def __init__(self, *, model: str = "nomic-embed-text", dimensions: int = 768,
                 base_url: str = "http://localhost:11434", transport: Transport | None = None,
                 enforce_dimensions: bool = True, timeout_seconds: float = 5.0) -> None:
        self.model = model
        self.dimensions = dimensions
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrllibTransport(timeout=timeout_seconds)
        self.enforce_dimensions = enforce_dimensions

    def _embed_one(self, text: str) -> list[float]:
        body = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        try:
            resp = self.transport.request("POST", f"{self.base_url}/api/embeddings",
                                          headers={"Content-Type": "application/json"}, body=body)
        except Exception as exc:  # noqa: BLE001 - network boundary
            raise OfflineError(f"ollama_unreachable: {exc}") from exc
        if resp.status >= 500:
            raise OfflineError(f"ollama_transient_{resp.status}")
        if resp.status >= 400:
            raise EmbeddingProviderError(f"ollama_error_{resp.status}")
        vec = resp.json().get("embedding")
        if not isinstance(vec, list) or not vec:
            raise EmbeddingProviderError("ollama_embedding_missing")
        if self.enforce_dimensions and len(vec) != self.dimensions:
            raise DimensionMismatchError(f"ollama_dim:expected={self.dimensions}:actual={len(vec)}")
        return [float(x) for x in vec]

    def embed(self, text: str) -> list[float]:
        return self._embed_one(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def health(self) -> ProviderHealth:
        try:
            v = self._embed_one("secondbrain health probe")
            return ProviderHealth("PASS", self.name, self.model, len(v), True, True)
        except Exception as exc:  # noqa: BLE001
            return ProviderHealth("FAIL", self.name, self.model, self.dimensions, True, False, str(exc))
