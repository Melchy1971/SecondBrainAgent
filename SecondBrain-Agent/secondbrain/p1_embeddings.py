from __future__ import annotations

import hashlib
import importlib
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


def _coerce_vector(raw: Any, *, error_code: str) -> list[float]:
    if not isinstance(raw, list) or not raw:
        raise RuntimeError(error_code)
    return _normalize([float(v) for v in raw])


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
        return {
            "ok": True,
            "provider": self.name,
            "dimensions": self.dimensions,
            "network": False,
            "mode": "local_test_double",
            "semantic": False,
            "fallback": None,
            "fallback_used": False,
            "production_ready": False,
            "reason": "deterministic local embeddings are for offline development and tests, not production semantic retrieval",
        }


@dataclass(frozen=True)
class OllamaEmbeddingProvider:
    model: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"
    dimensions: int = DEFAULT_DIMENSIONS
    timeout_seconds: float = 2.0
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    name: str = "ollama"

    def _request_embedding(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = request.Request(f"{self.base_url.rstrip('/')}/api/embeddings", data=payload, headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec - local/user configured endpoint
            data = json.loads(response.read().decode("utf-8"))
        return _coerce_vector(data.get("embedding"), error_code="ollama_embedding_missing")

    def embed(self, text: str) -> list[float]:
        try:
            return self._request_embedding(text)
        except Exception:
            return self.fallback.embed(text)

    def status(self) -> dict[str, Any]:
        try:
            vector = self._request_embedding("secondbrain health probe")
            return {
                "ok": True,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "dimensions": len(vector),
                "configured_dimensions": self.dimensions,
                "fallback": self.fallback.name,
                "fallback_used": False,
                "network": True,
                "semantic": True,
                "production_ready": True,
            }
        except Exception as exc:  # noqa: BLE001 - provider health boundary
            return {
                "ok": False,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "dimensions": self.dimensions,
                "fallback": self.fallback.name,
                "fallback_used": True,
                "network": True,
                "semantic": True,
                "production_ready": False,
                "error": str(exc),
                "reason": "ollama embedding endpoint unavailable or returned invalid vector",
            }


@dataclass(frozen=True)
class OpenAIEmbeddingProvider:
    model: str = "text-embedding-3-small"
    api_key_env: str = "OPENAI_API_KEY"
    dimensions: int = DEFAULT_DIMENSIONS
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    name: str = "openai"

    def _api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip()

    def _client(self) -> Any:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError("openai_api_key_missing")
        try:
            module = importlib.import_module("openai")
        except Exception as exc:  # noqa: BLE001 - optional dependency boundary
            raise RuntimeError("openai_sdk_missing") from exc
        client_cls = getattr(module, "OpenAI", None)
        if client_cls is None:
            raise RuntimeError("openai_client_class_missing")
        return client_cls(api_key=api_key)

    def _request_embedding(self, text: str) -> list[float]:
        client = self._client()
        response = client.embeddings.create(model=self.model, input=text or " ")
        try:
            raw_vector = response.data[0].embedding
        except Exception as exc:  # noqa: BLE001 - SDK response boundary
            raise RuntimeError("openai_embedding_missing") from exc
        return _coerce_vector(raw_vector, error_code="openai_embedding_missing")

    def embed(self, text: str) -> list[float]:
        try:
            return self._request_embedding(text)
        except Exception:
            return self.fallback.embed(text)

    def status(self) -> dict[str, Any]:
        api_key_configured = bool(self._api_key())
        try:
            vector = self._request_embedding("secondbrain health probe")
            return {
                "ok": True,
                "provider": self.name,
                "model": self.model,
                "api_key_configured": api_key_configured,
                "dimensions": len(vector),
                "configured_dimensions": self.dimensions,
                "fallback": self.fallback.name,
                "fallback_used": False,
                "network": True,
                "semantic": True,
                "production_ready": True,
            }
        except Exception as exc:  # noqa: BLE001 - provider health boundary
            return {
                "ok": False,
                "provider": self.name,
                "model": self.model,
                "api_key_configured": api_key_configured,
                "dimensions": self.dimensions,
                "fallback": self.fallback.name,
                "fallback_used": True,
                "network": True,
                "semantic": True,
                "production_ready": False,
                "error": str(exc),
                "reason": "OpenAI embeddings require openai SDK, API key and a successful embeddings health probe",
            }


def provider_from_profile(project_root: str | Path, profile: str | None = None) -> EmbeddingProvider:
    root = Path(project_root)
    config_path = root / "config" / "vector_rag.yaml"
    provider = os.getenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local").strip().lower()
    model = os.getenv("SECONDBRAIN_EMBEDDING_MODEL", "").strip()
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8", errors="ignore").lower()
        if "embedding_provider: ollama" in text or "provider: ollama" in text:
            provider = "ollama"
        elif "embedding_provider: openai" in text or "provider: openai" in text:
            provider = "openai"
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("embedding_model:") or line.startswith("model:"):
                model = line.split(":", 1)[1].strip().strip('"\'')
                break
    if provider == "ollama":
        return OllamaEmbeddingProvider(model=model or "nomic-embed-text")
    if provider == "openai":
        return OpenAIEmbeddingProvider(model=model or "text-embedding-3-small")
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
