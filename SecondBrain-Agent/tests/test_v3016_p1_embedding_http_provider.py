from __future__ import annotations

import json
from urllib import error

import pytest

from secondbrain import p1_embeddings
from secondbrain.p1_embedding_config import load_embedding_config
from secondbrain.p1_embeddings import OpenAIEmbeddingProvider, provider_from_profile


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_openai_provider_uses_native_http_when_sdk_missing(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["auth"] = req.headers.get("Authorization")
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _FakeHTTPResponse({"data": [{"embedding": [1.0, 0.0, 0.0, 0.0]}]})

    monkeypatch.setattr(OpenAIEmbeddingProvider, "_sdk_client", lambda self: None)
    monkeypatch.setattr(p1_embeddings.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    provider = OpenAIEmbeddingProvider(dimensions=4, enforce_dimensions=True, timeout_seconds=3.5)
    status = provider.status()

    assert status["ok"] is True
    assert status["transport"] == "http"
    assert status["dimension_contract_ok"] is True
    assert seen["url"] == "https://api.openai.com/v1/embeddings"
    assert seen["timeout"] == 3.5
    assert seen["auth"] == "Bearer test-key"
    assert seen["body"]["model"] == "text-embedding-3-small"


def test_openai_http_error_is_reported_without_local_fallback(monkeypatch):
    def fake_urlopen(req, timeout):
        raise error.URLError("network down")

    monkeypatch.setattr(OpenAIEmbeddingProvider, "_sdk_client", lambda self: None)
    monkeypatch.setattr(p1_embeddings.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    provider = OpenAIEmbeddingProvider(dimensions=4, enforce_dimensions=True, allow_fallback=False)
    status = provider.status()

    assert status["ok"] is False
    assert status["fallback_used"] is False
    assert status["production_ready"] is False
    assert "openai_network_error" in status["error"]
    with pytest.raises(RuntimeError, match="openai_embedding_unavailable"):
        provider.embed("hello")


def test_embedding_timeout_config_is_passed_to_provider(monkeypatch, tmp_path):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "4")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS", "7.25")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    cfg = load_embedding_config(tmp_path)
    provider = provider_from_profile(tmp_path)

    assert cfg.timeout_seconds == 7.25
    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.timeout_seconds == 7.25
