from __future__ import annotations

import sys
import types

from secondbrain.p1_embedding_config import evaluate_embedding_config, load_embedding_config
from secondbrain.p1_embeddings import OpenAIEmbeddingProvider, provider_from_profile
from secondbrain.p1_provider_health import evaluate_embedding_provider_health
from secondbrain.p1_rag_runtime import P1RagRuntime


class _FakeEmbedding:
    def __init__(self, values):
        self.embedding = values


class _FakeResponse:
    def __init__(self, values):
        self.data = [_FakeEmbedding(values)]


def _fake_openai_module(values):
    class _Embeddings:
        def create(self, *, model, input):
            return _FakeResponse(values)

    class _Client:
        def __init__(self, *, api_key):
            self.embeddings = _Embeddings()

    return types.SimpleNamespace(OpenAI=_Client)


def test_provider_defaults_use_real_model_dimensions(monkeypatch, tmp_path):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", raising=False)
    cfg = load_embedding_config(tmp_path)

    assert cfg.dimensions == 1536
    assert cfg.dimensions_source == "provider_default"

    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "ollama")
    cfg = load_embedding_config(tmp_path)
    assert cfg.dimensions == 768
    assert cfg.dimensions_source == "provider_default"


def test_provider_from_profile_enforces_dimension_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "4")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", _fake_openai_module([1.0, 2.0, 3.0, 4.0]))

    provider = provider_from_profile(tmp_path)
    status = provider.status()

    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.enforce_dimensions is True
    assert status["ok"] is True
    assert status["dimension_contract_ok"] is True
    assert status["configured_dimensions"] == 4


def test_provider_health_blocks_dimension_mismatch(monkeypatch, tmp_path):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "5")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", _fake_openai_module([1.0, 2.0, 3.0, 4.0]))

    rt = P1RagRuntime(tmp_path)
    payload = evaluate_embedding_provider_health(rt, production=True)

    assert payload["ok"] is False
    assert "embedding_dimension_contract_failed" in payload["blockers"]
    assert payload["provider_status"]["dimension_contract_ok"] is False
    assert "openai_embedding_dimension_mismatch" in payload["provider_status"]["error"]


def test_embedding_config_report_schema_v2(monkeypatch, tmp_path):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "1536")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    payload = evaluate_embedding_config(tmp_path, production=True, write_report=True)

    assert payload["schema"] == "secondbrain.p1_embedding_config.v1"
    assert payload["ok"] is True
    assert payload["config"]["dimensions_source"] == "explicit"
