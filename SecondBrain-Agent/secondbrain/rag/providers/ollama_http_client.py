"""HTTP client for Ollama embeddings.

Dependency-free implementation using urllib so the core package remains installable
without optional HTTP libraries. Supports both Ollama embedding endpoint variants:
/api/embed and /api/embeddings.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OllamaEmbeddingError(RuntimeError):
    """Raised when Ollama embedding generation fails."""


class OllamaHttpClient:
    def __init__(self, host: str = "http://localhost:11434", timeout: float = 30.0) -> None:
        self.host = host.rstrip("/")
        self.timeout = float(timeout)

    def embed(self, texts: list[str], model: str = "nomic-embed-text") -> list[list[float]]:
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")
        if not texts:
            return []
        normalized = [str(text) for text in texts]

        # Newer Ollama endpoint: accepts input as list and returns embeddings.
        try:
            response = self._post_json("/api/embed", {"model": model, "input": normalized})
            vectors = response.get("embeddings")
            if vectors is not None:
                return _validate_vectors(vectors, expected=len(normalized))
        except OllamaEmbeddingError:
            # Fall back to legacy endpoint below. Keep the original error hidden only
            # because many installations expose exactly one of the two endpoints.
            pass

        # Legacy endpoint: one prompt per request, returns embedding.
        result: list[list[float]] = []
        for text in normalized:
            response = self._post_json("/api/embeddings", {"model": model, "prompt": text})
            result.append(_validate_vector(response.get("embedding")))
        return result

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.host}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # nosec B310 - configurable local/user endpoint
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise OllamaEmbeddingError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OllamaEmbeddingError(f"Ollama unavailable: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OllamaEmbeddingError("Ollama request timed out") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OllamaEmbeddingError("Ollama returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise OllamaEmbeddingError("Ollama returned unexpected payload")
        return data


def _validate_vector(vector: Any) -> list[float]:
    if not isinstance(vector, list) or not vector:
        raise OllamaEmbeddingError("Ollama response does not contain a non-empty embedding")
    try:
        return [float(value) for value in vector]
    except (TypeError, ValueError) as exc:
        raise OllamaEmbeddingError("Ollama embedding contains non-numeric values") from exc


def _validate_vectors(vectors: Any, *, expected: int) -> list[list[float]]:
    if not isinstance(vectors, list) or len(vectors) != expected:
        raise OllamaEmbeddingError("Ollama response embedding count does not match request")
    return [_validate_vector(vector) for vector in vectors]
