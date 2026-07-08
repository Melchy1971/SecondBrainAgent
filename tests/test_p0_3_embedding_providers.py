from secondbrain.rag.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from secondbrain.rag.providers.openai_embedding_provider import OpenAIEmbeddingProvider
from secondbrain.rag.providers.openai_http_client import OpenAIEmbeddingError, OpenAIHttpClient


class FakeClient:
    def __init__(self):
        self.calls = []

    def embed(self, texts, model):
        self.calls.append((texts, model))
        return [[float(len(text)), 1.0] for text in texts]


def test_ollama_provider_delegates_to_client():
    client = FakeClient()
    provider = OllamaEmbeddingProvider(model="unit-model", client=client)

    assert provider.embed(["a", "abcd"]) == [[1.0, 1.0], [4.0, 1.0]]
    assert client.calls == [(["a", "abcd"], "unit-model")]


def test_openai_provider_delegates_to_client():
    client = FakeClient()
    provider = OpenAIEmbeddingProvider(model="unit-openai", client=client)

    assert provider.embed(["hello"]) == [[5.0, 1.0]]
    assert client.calls == [(["hello"], "unit-openai")]


def test_openai_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = OpenAIHttpClient(api_key=None)

    try:
        client.embed(["hello"], model="x")
    except OpenAIEmbeddingError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected OpenAIEmbeddingError")


def test_embedding_providers_return_empty_batch_without_network():
    assert OllamaEmbeddingProvider(client=FakeClient()).embed([]) == []
    assert OpenAIEmbeddingProvider(client=FakeClient()).embed([]) == []
