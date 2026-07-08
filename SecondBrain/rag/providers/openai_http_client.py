"""HTTP client for OpenAI-compatible embeddings."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenAIEmbeddingError(RuntimeError):
    """Raised when OpenAI-compatible embedding generation fails."""


class OpenAIHttpClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")
        if not texts:
            return []
        if not self.api_key:
            raise OpenAIEmbeddingError("OPENAI_API_KEY is required for OpenAI embeddings")

        payload = {"model": model, "input": [str(text) for text in texts]}
        data = self._post_json("/embeddings", payload)
        rows = data.get("data")
        if not isinstance(rows, list) or len(rows) != len(texts):
            raise OpenAIEmbeddingError("OpenAI response embedding count does not match request")

        rows_by_index = sorted(rows, key=lambda item: int(item.get("index", 0)))
        return [_validate_vector(row.get("embedding")) for row in rows_by_index]

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # nosec B310 - official/configurable endpoint
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise OpenAIEmbeddingError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise OpenAIEmbeddingError(f"OpenAI unavailable: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OpenAIEmbeddingError("OpenAI request timed out") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OpenAIEmbeddingError("OpenAI returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise OpenAIEmbeddingError("OpenAI returned unexpected payload")
        return data


def _validate_vector(vector: Any) -> list[float]:
    if not isinstance(vector, list) or not vector:
        raise OpenAIEmbeddingError("OpenAI response does not contain a non-empty embedding")
    try:
        return [float(value) for value in vector]
    except (TypeError, ValueError) as exc:
        raise OpenAIEmbeddingError("OpenAI embedding contains non-numeric values") from exc
