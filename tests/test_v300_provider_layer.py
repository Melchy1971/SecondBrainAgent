from secondbrain.providers.base.provider_models import ChatMessage, CompletionRequest, EmbeddingRequest
from secondbrain.providers.openai.chat_provider import OpenAIProvider
from secondbrain.providers.ollama.chat_provider import OllamaProvider
from secondbrain.providers.routing.provider_cost_tracker import Pricing, ProviderCostTracker
from secondbrain.providers.routing.provider_manager import ProviderManager
from secondbrain.providers.routing.provider_rate_limiter import ProviderRateLimiter


class FakeResponse:
    def __init__(self, data):
        self.status_code = 200
        self.data = data


class FakeTransport:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def post_json(self, url, payload, headers=None, timeout=60.0):
        self.calls.append((url, payload, headers or {}))
        return FakeResponse(self.data)


def test_openai_completion_maps_response():
    transport = FakeTransport({
        "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    })
    provider = OpenAIProvider(api_key="x", transport=transport)
    response = provider.complete(CompletionRequest(model="gpt-test", messages=[ChatMessage("user", "Hi")]))
    assert response.provider == "openai"
    assert response.content == "hello"
    assert transport.calls[0][2]["Authorization"] == "Bearer x"


def test_ollama_embedding_maps_response():
    transport = FakeTransport({"embeddings": [[1, 2, 3], [4, 5, 6]]})
    provider = OllamaProvider(transport=transport)
    response = provider.embed(EmbeddingRequest(model="nomic", texts=["a", "b"]))
    assert response.vectors == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_provider_manager_registers_and_routes():
    transport = FakeTransport({"choices": [{"message": {"content": "ok"}}]})
    manager = ProviderManager(rate_limiter=ProviderRateLimiter(max_calls=10))
    manager.register(OpenAIProvider(api_key="x", transport=transport))
    response = manager.complete("openai", CompletionRequest(model="gpt-test", messages=[ChatMessage("user", "Hi")]))
    assert response.content == "ok"
    assert manager.list() == ["openai"]
    assert manager.metrics.summary()["calls"] == 1


def test_cost_tracker_estimates_model_cost():
    tracker = ProviderCostTracker({"m": Pricing(input_per_1m=1.0, output_per_1m=2.0)})
    assert tracker.estimate("m", input_tokens=1_000_000, output_tokens=500_000) == 2.0
