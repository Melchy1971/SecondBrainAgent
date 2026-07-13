from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib import error, request

from secondbrain.p1_embedding_config import load_embedding_config


DEFAULT_DIMENSIONS = 64
FALLBACK_ENV = "SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK"


class EmbeddingProvider(Protocol):
    name: str
    dimensions: int

    def embed(self, text: str) -> list[float]:
        ...

    def status(self) -> dict[str, Any]:
        ...


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm <= 0:
        return vector
    return [round(v / norm, 8) for v in vector]


def _coerce_vector(raw: Any, *, error_code: str) -> list[float]:
    if not isinstance(raw, list) or not raw:
        raise RuntimeError(error_code)
    return _normalize([float(v) for v in raw])




def embedding_index_provider(provider: Any) -> str:
    """Stable vector index identity for provider/model/dimension migrations.

    Store vectors under a key that includes the semantic model contract, not only
    the vendor name. This prevents OpenAI/Ollama model swaps with the same
    provider label from silently mixing incompatible embeddings.
    """
    status = provider.status() if hasattr(provider, "status") else {}
    base = str(status.get("provider") or getattr(provider, "name", "unknown")).strip() or "unknown"
    model = str(status.get("model") or getattr(provider, "model", "default")).strip() or "default"
    dimensions = int(status.get("configured_dimensions") or status.get("dimensions") or getattr(provider, "dimensions", 0) or 0)
    return f"{base}:{model}:{dimensions}"

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
            "index_provider": f"{self.name}:default:{self.dimensions}",
            "dimensions": self.dimensions,
            "network": False,
            "mode": "local_test_double",
            "semantic": False,
            "fallback": None,
            "fallback_used": False,
            "fallback_allowed": False,
            "production_ready": False,
            "reason": "deterministic local embeddings are for offline development and tests, not production semantic retrieval",
        }


@dataclass(frozen=True)
class OllamaEmbeddingProvider:
    model: str = "nomic-embed-text"
    base_url: str = "http://localhost:11434"
    dimensions: int = DEFAULT_DIMENSIONS
    timeout_seconds: float = 2.0
    enforce_dimensions: bool = False
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    allow_fallback: bool = False
    name: str = "ollama"

    def _fallback_allowed(self) -> bool:
        return bool(self.allow_fallback or _env_flag(FALLBACK_ENV, False))

    def _request_embedding(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = request.Request(f"{self.base_url.rstrip('/')}/api/embeddings", data=payload, headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec - local/user configured endpoint
            data = json.loads(response.read().decode("utf-8"))
        vector = _coerce_vector(data.get("embedding"), error_code="ollama_embedding_missing")
        if self.enforce_dimensions and len(vector) != int(self.dimensions):
            raise RuntimeError(f"ollama_embedding_dimension_mismatch:expected={self.dimensions}:actual={len(vector)}")
        return vector

    def embed(self, text: str) -> list[float]:
        try:
            return self._request_embedding(text)
        except Exception as exc:  # noqa: BLE001 - provider boundary
            if self._fallback_allowed():
                return LocalEmbeddingProvider(self.dimensions).embed(text)
            raise RuntimeError("ollama_embedding_unavailable") from exc

    def status(self) -> dict[str, Any]:
        fallback_allowed = self._fallback_allowed()
        try:
            vector = self._request_embedding("secondbrain health probe")
            return {
                "ok": True,
                "provider": self.name,
                "index_provider": f"{self.name}:{self.model}:{len(vector)}",
                "model": self.model,
                "base_url": self.base_url,
                "dimensions": len(vector),
                "configured_dimensions": self.dimensions,
                "dimension_contract_ok": (len(vector) == int(self.dimensions)) if self.enforce_dimensions else None,
                "enforce_dimensions": self.enforce_dimensions,
                "fallback": self.fallback.name,
                "fallback_used": False,
                "fallback_allowed": fallback_allowed,
                "network": True,
                "semantic": True,
                "production_ready": True,
            }
        except Exception as exc:  # noqa: BLE001 - provider health boundary
            return {
                "ok": False,
                "provider": self.name,
                "index_provider": f"{self.name}:{self.model}:{self.dimensions}",
                "model": self.model,
                "base_url": self.base_url,
                "dimensions": self.dimensions,
                "configured_dimensions": self.dimensions,
                "dimension_contract_ok": False if self.enforce_dimensions else None,
                "enforce_dimensions": self.enforce_dimensions,
                "fallback": self.fallback.name,
                "fallback_used": fallback_allowed,
                "fallback_allowed": fallback_allowed,
                "network": True,
                "semantic": True,
                "production_ready": False,
                "error": str(exc),
                "reason": "ollama embedding endpoint unavailable or returned invalid vector; ingest/reindex blocks unless SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true",
            }


@dataclass(frozen=True)
class OpenAIEmbeddingProvider:
    model: str = "text-embedding-3-small"
    api_key_env: str = "OPENAI_API_KEY"
    dimensions: int = DEFAULT_DIMENSIONS
    timeout_seconds: float = 10.0
    enforce_dimensions: bool = False
    fallback: LocalEmbeddingProvider = LocalEmbeddingProvider()
    allow_fallback: bool = False
    name: str = "openai"

    def _fallback_allowed(self) -> bool:
        return bool(self.allow_fallback or _env_flag(FALLBACK_ENV, False))

    def _api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip()

    def _sdk_client(self) -> Any | None:
        """Return optional OpenAI SDK client when installed.

        The provider is production-capable without the SDK by using the HTTPS
        embeddings API directly. This keeps deployments smaller and removes the
        previous hard dependency on the optional `openai` package. Existing SDK
        test doubles still work because the SDK path is preferred when present.
        """
        try:
            module = importlib.import_module("openai")
        except Exception:  # noqa: BLE001 - optional dependency boundary
            return None
        client_cls = getattr(module, "OpenAI", None)
        if client_cls is None:
            return None
        return client_cls(api_key=self._api_key())

    def _request_embedding_sdk(self, text: str) -> list[float]:
        client = self._sdk_client()
        if client is None:
            raise RuntimeError("openai_sdk_unavailable")
        response = client.embeddings.create(model=self.model, input=text or " ")
        try:
            raw_vector = response.data[0].embedding
        except Exception as exc:  # noqa: BLE001 - SDK response boundary
            raise RuntimeError("openai_embedding_missing") from exc
        return _coerce_vector(raw_vector, error_code="openai_embedding_missing")

    def _request_embedding_http(self, text: str) -> list[float]:
        payload = json.dumps({"model": self.model, "input": text or " "}).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/embeddings",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec - official HTTPS endpoint
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")[:500]
            raise RuntimeError(f"openai_http_error:{exc.code}:{body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"openai_network_error:{exc.reason}") from exc
        try:
            raw_vector = data["data"][0]["embedding"]
        except Exception as exc:  # noqa: BLE001 - HTTP response boundary
            raise RuntimeError("openai_embedding_missing") from exc
        return _coerce_vector(raw_vector, error_code="openai_embedding_missing")

    def _request_embedding(self, text: str) -> list[float]:
        if not self._api_key():
            raise RuntimeError("openai_api_key_missing")
        if "openai" in sys.modules and sys.modules["openai"] is None:
            raise RuntimeError("openai_sdk_missing")
        try:
            vector = self._request_embedding_sdk(text)
            transport = "sdk"
        except RuntimeError as exc:
            if str(exc) != "openai_sdk_unavailable":
                raise
            vector = self._request_embedding_http(text)
            transport = "http"
        if self.enforce_dimensions and len(vector) != int(self.dimensions):
            raise RuntimeError(f"openai_embedding_dimension_mismatch:expected={self.dimensions}:actual={len(vector)}")
        object.__setattr__(self, "_last_transport", transport)
        return vector

    def embed(self, text: str) -> list[float]:
        try:
            return self._request_embedding(text)
        except Exception as exc:  # noqa: BLE001 - provider boundary
            if self._fallback_allowed():
                return LocalEmbeddingProvider(self.dimensions).embed(text)
            raise RuntimeError("openai_embedding_unavailable") from exc

    def status(self) -> dict[str, Any]:
        api_key_configured = bool(self._api_key())
        fallback_allowed = self._fallback_allowed()
        try:
            vector = self._request_embedding("secondbrain health probe")
            return {
                "ok": True,
                "provider": self.name,
                "index_provider": f"{self.name}:{self.model}:{len(vector)}",
                "model": self.model,
                "api_key_configured": api_key_configured,
                "transport": getattr(self, "_last_transport", None) or "unknown",
                "dimensions": len(vector),
                "configured_dimensions": self.dimensions,
                "dimension_contract_ok": (len(vector) == int(self.dimensions)) if self.enforce_dimensions else None,
                "enforce_dimensions": self.enforce_dimensions,
                "fallback": self.fallback.name,
                "fallback_used": False,
                "fallback_allowed": fallback_allowed,
                "network": True,
                "semantic": True,
                "production_ready": True,
            }
        except Exception as exc:  # noqa: BLE001 - provider health boundary
            return {
                "ok": False,
                "provider": self.name,
                "index_provider": f"{self.name}:{self.model}:{self.dimensions}",
                "model": self.model,
                "api_key_configured": api_key_configured,
                "transport": getattr(self, "_last_transport", None) or "unavailable",
                "dimensions": self.dimensions,
                "configured_dimensions": self.dimensions,
                "dimension_contract_ok": False if self.enforce_dimensions else None,
                "enforce_dimensions": self.enforce_dimensions,
                "fallback": self.fallback.name,
                "fallback_used": fallback_allowed,
                "fallback_allowed": fallback_allowed,
                "network": True,
                "semantic": True,
                "production_ready": False,
                "error": str(exc),
                "reason": "OpenAI embeddings require an API key and a successful SDK or HTTPS embeddings health probe; ingest/reindex blocks unless SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true",
            }


def provider_from_profile(project_root: str | Path, profile: str | None = None) -> EmbeddingProvider:
    cfg = load_embedding_config(project_root, profile)
    if cfg.provider == "ollama":
        return OllamaEmbeddingProvider(
            model=cfg.model or "nomic-embed-text",
            base_url=cfg.ollama_base_url,
            dimensions=cfg.dimensions,
            timeout_seconds=cfg.timeout_seconds,
            allow_fallback=cfg.allow_fallback,
            enforce_dimensions=True,
        )
    if cfg.provider == "openai":
        return OpenAIEmbeddingProvider(
            model=cfg.model or "text-embedding-3-small",
            api_key_env=cfg.openai_api_key_env,
            dimensions=cfg.dimensions,
            timeout_seconds=cfg.timeout_seconds,
            allow_fallback=cfg.allow_fallback,
            enforce_dimensions=True,
        )
    return LocalEmbeddingProvider(dimensions=cfg.dimensions)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    size = min(len(a), len(b))
    numerator = sum(a[i] * b[i] for i in range(size))
    da = math.sqrt(sum(a[i] * a[i] for i in range(size)))
    db = math.sqrt(sum(b[i] * b[i] for i in range(size)))
    if da <= 0 or db <= 0:
        return 0.0
    return round(numerator / (da * db), 8)
