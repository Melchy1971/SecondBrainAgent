import pytest
from secondbrain.connectors.scaffold.transport import FakeTransport
from secondbrain.embeddings.providers import OpenAIEmbeddingProvider, OllamaEmbeddingProvider, LocalEmbeddingProvider
from secondbrain.embeddings.base import EmbeddingProviderError, OfflineError, DimensionMismatchError


def _openai(tp, **kw):
    return OpenAIEmbeddingProvider(model="m", dimensions=4, api_key="k", transport=tp, **kw)


def test_openai_embed_and_batch():
    tp = FakeTransport().on("POST", "/v1/embeddings",
        lambda u, m, h, b: tp0.json_response(200, {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4]}]}))
    global tp0; tp0 = tp
    p = _openai(tp)
    assert p.embed("hi") == [0.1, 0.2, 0.3, 0.4]


def test_openai_missing_key_raises_not_fake():
    import os
    os.environ.pop("OPENAI_API_KEY", None)
    p = OpenAIEmbeddingProvider(model="m", dimensions=4, transport=FakeTransport())
    with pytest.raises(EmbeddingProviderError):
        p.embed("hi")               # must NOT return fake vectors


def test_openai_dimension_mismatch():
    tp = FakeTransport()
    tp.on("POST", "/v1/embeddings", lambda u, m, h, b: tp.json_response(200, {"data": [{"embedding": [0.1, 0.2]}]}))
    with pytest.raises(DimensionMismatchError):
        _openai(tp).embed("hi")


def test_openai_5xx_is_offline_and_401_is_error():
    tp = FakeTransport()
    tp.on("POST", "/v1/embeddings", lambda u, m, h, b: tp.json_response(503, {"error": "down"}))
    with pytest.raises(OfflineError):
        _openai(tp).embed("hi")
    tp2 = FakeTransport()
    tp2.on("POST", "/v1/embeddings", lambda u, m, h, b: tp2.json_response(401, {"error": "no"}))
    with pytest.raises(EmbeddingProviderError):
        OpenAIEmbeddingProvider(model="m", dimensions=4, api_key="k", transport=tp2).embed("hi")


def test_ollama_embed_and_health():
    tp = FakeTransport()
    tp.on("POST", "/api/embeddings", lambda u, m, h, b: tp.json_response(200, {"embedding": [0.1, 0.2, 0.3]}))
    p = OllamaEmbeddingProvider(model="nomic", dimensions=3, transport=tp)
    assert p.embed("x") == [0.1, 0.2, 0.3]
    assert p.health().status == "PASS"


def test_local_is_never_production_ready():
    h = LocalEmbeddingProvider(dimensions=8).health()
    assert h.production_ready is False and h.semantic is False
