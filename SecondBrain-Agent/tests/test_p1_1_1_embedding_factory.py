from __future__ import annotations

import pytest

from secondbrain.rag.providers import (
    DeterministicEmbeddingProvider,
    EmbeddingBatch,
    EmbeddingFactory,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
    GeminiEmbeddingProvider,
    normalize_vectors,
)


class FakeClient:
    def __init__(self, vectors=None):
        self.calls = []
        self.vectors = vectors or [[1.0, 2.0], [3.0, 4.0]]

    def embed(self, texts, model):
        self.calls.append((texts, model))
        return self.vectors[: len(texts)]


def test_factory_creates_deterministic_provider_from_dict():
    provider = EmbeddingFactory.create(settings={"provider": "deterministic", "dimensions": 12})
    vectors = provider.embed(["alpha", "alpha", "beta"])

    assert isinstance(provider, DeterministicEmbeddingProvider)
    assert len(vectors) == 3
    assert len(vectors[0]) == 12
    assert vectors[0] == vectors[1]
    assert vectors[0] != vectors[2]


def test_factory_creates_ollama_provider_with_injected_client():
    client = FakeClient(vectors=[[0.1, 0.2]])
    provider = EmbeddingFactory.create("ollama", {"model": "unit-ollama", "client": client})

    assert provider.embed(["one"]) == [[0.1, 0.2]]
    assert client.calls == [(["one"], "unit-ollama")]


def test_factory_creates_openai_provider_with_injected_client():
    client = FakeClient(vectors=[[0.7, 0.8]])
    provider = EmbeddingFactory.create("openai", {"model": "unit-openai", "client": client})

    assert provider.embed(["one"]) == [[0.7, 0.8]]
    assert client.calls == [(["one"], "unit-openai")]


def test_gemini_provider_uses_injected_client_and_validates_output(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = FakeClient(vectors=[[1, 2], [3, 4]])
    provider = GeminiEmbeddingProvider(model="unit-gemini", client=client)

    assert provider.embed(["a", "b"]) == [[1.0, 2.0], [3.0, 4.0]]
    assert client.calls == [(["a", "b"], "unit-gemini")]


def test_embed_batch_returns_normalized_metadata():
    provider = EmbeddingFactory.create(settings=EmbeddingProviderConfig(provider="deterministic", dimensions=8, model="unit-hash"))
    result = provider.embed_batch(EmbeddingBatch(texts=["context"], model="override-model"))

    assert result.provider == "deterministic"
    assert result.model == "override-model"
    assert result.dimensions == 8
    assert len(result.vectors) == 1


def test_normalize_vectors_rejects_malformed_provider_output():
    with pytest.raises(EmbeddingProviderError):
        normalize_vectors([[1.0], [1.0, 2.0]], expected_count=2)
    with pytest.raises(EmbeddingProviderError):
        normalize_vectors([["x"]], expected_count=1)
    with pytest.raises(EmbeddingProviderError):
        normalize_vectors([[1.0]], expected_count=2)


def test_unknown_provider_fails_fast():
    with pytest.raises(EmbeddingProviderError):
        EmbeddingFactory.create("missing-provider", {})
