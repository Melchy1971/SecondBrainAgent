import io
import json
from urllib.error import HTTPError

import pytest

from secondbrain.providers.base.http_transport import HttpResponse, JsonHttpTransport
from secondbrain.providers.base.provider_exception import ProviderError
from secondbrain.providers.base.provider_models import CompletionRequest, ChatMessage
from secondbrain.providers.ollama.chat_provider import OllamaProvider
from secondbrain.providers.openai.chat_provider import OpenAIProvider
from secondbrain.release.provider_live_gate import run_provider_live_gate, _safe_error, probe_provider


class CaptureTransport:
    def post_json(self, url, payload, headers=None):
        self.payload = payload
        return HttpResponse(200, {"message": {"content": '{"live":true}'},
                                  "choices": [{"message": {"content": '{"live":true}'}}]})


def test_ollama_preserves_token_limit_finish_reason():
    class Transport:
        def post_json(self, *args):
            return HttpResponse(200, {"message": {"content": '{"live":true}'}, "done": True, "done_reason": "length"})
    response = OllamaProvider(transport=Transport()).complete(CompletionRequest("test", []))
    assert response.finish_reason == "length"


@pytest.mark.parametrize("provider", ["ollama", "openai"])
def test_explicit_json_format_and_token_budget(provider):
    transport = CaptureTransport()
    adapter = OllamaProvider(transport=transport) if provider == "ollama" else OpenAIProvider(api_key="test", transport=transport)
    adapter.complete(CompletionRequest("test", [ChatMessage("user", "JSON")], max_tokens=64, response_format="json_object"))
    if provider == "ollama":
        assert transport.payload["format"] == "json"
        assert transport.payload["options"]["num_predict"] == 64
    else:
        assert transport.payload["response_format"] == {"type": "json_object"}
        assert transport.payload["max_tokens"] == 64


@pytest.mark.parametrize("code,retryable", [("insufficient_quota", False), ("rate_limit_exceeded", True), ("private-secret", True)])
def test_429_classification_is_redacted(monkeypatch, code, retryable):
    def fail(*args, **kwargs):
        raise HTTPError("https://private", 429, "private-secret", {}, io.BytesIO(json.dumps({"error": {"code": code, "message": "private-secret"}}).encode()))
    monkeypatch.setattr("secondbrain.providers.base.http_transport.urlrequest.urlopen", fail)
    with pytest.raises(ProviderError) as caught:
        JsonHttpTransport().post_json("https://test", {})
    assert caught.value.retryable is retryable
    report = _safe_error(caught.value)
    assert report["error_kind"] == (code if code != "private-secret" else "rate_limit")
    assert "private-secret" not in str(caught.value) + json.dumps(report)


def test_degraded_required_provider_blocks(tmp_path):
    report = run_provider_live_gate(tmp_path, env={"OLLAMA_LIVE_MODEL": "test", "REQUIRED_LIVE_PROVIDERS": "ollama"},
                                    probe=lambda *_: {"name": "ollama", "readiness": "degraded"})
    assert report["status"] == "BLOCKED"
    assert report["failed_providers"] == ["ollama"]


@pytest.mark.parametrize("content,finish,expected", [
    ('{"live":true}', "stop", "ready"),
    ('{"live":1}', "stop", "degraded"),
    ('{"live":true,"extra":1}', "stop", "degraded"),
    ('{"live":true}', "length", "degraded"),
    ('[true]', "stop", "degraded"),
    ('null', "stop", "degraded"),
    ('{"live":', "length", "degraded"),
])
def test_probe_requests_json_mode(monkeypatch, content, finish, expected):
    class Adapter:
        capabilities = OllamaProvider.capabilities
        def complete(self, request):
            assert request.response_format == "json_object" and request.max_tokens == 64
            from secondbrain.providers.base.provider_models import CompletionResponse
            return CompletionResponse("ollama", "test", content, finish_reason=finish)
        def embed(self, request):
            from secondbrain.providers.base.provider_models import EmbeddingResponse
            return EmbeddingResponse("ollama", "embedding", [[1.0, 2.0]])
    monkeypatch.setattr("secondbrain.release.provider_live_gate._provider", lambda *_: Adapter())
    result = probe_provider({"name": "ollama", "model": "test", "embedding_model": "embedding", "timeout": 20, "source": "local"}, {})
    assert result["readiness"] == expected


@pytest.mark.parametrize("key,value", [
    ("PROVIDER_LIVE_TIMEOUT_SECONDS", "nan"),
    ("PROVIDER_LIVE_TIMEOUT_SECONDS", "inf"),
    ("PROVIDER_LIVE_TIMEOUT_SECONDS", "0"),
    ("PROVIDER_LIVE_MAX_COST", "nan"),
    ("PROVIDER_LIVE_MAX_COST", "inf"),
    ("PROVIDER_LIVE_MAX_COST", "-1"),
])
def test_invalid_numeric_configuration_blocks(tmp_path, key, value):
    report = run_provider_live_gate(tmp_path, env={key: value})
    assert report["status"] == "BLOCKED"
    assert report["configuration_error"] == "invalid_numeric_setting"


@pytest.mark.parametrize("cost", [float("nan"), float("inf"), -1])
def test_invalid_probe_cost_blocks(tmp_path, cost):
    report = run_provider_live_gate(tmp_path, env={"OLLAMA_LIVE_MODEL": "test"},
        probe=lambda *_: {"name": "ollama", "readiness": "ready", "estimated_cost": cost})
    assert report["status"] == "BLOCKED"
    assert report["providers"][1]["error_code"] == "invalid_probe_cost"
