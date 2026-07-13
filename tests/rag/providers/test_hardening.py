"""Hardening tests for the RAG embedding-provider stack (Task 1).

Covers every provider state the acceptance criteria name:
- deterministic/local is DEV_ONLY and blocked in production (no silent fake)
- OpenAI/Ollama offline produce FAIL, never a silent fallback vector
- dimension mismatch is detected
- model validation rejects disallowed models
- provider-identity change requires a reindex
- the production gate blocks dev-only and unknown providers
"""

from __future__ import annotations

import pytest

from secondbrain.rag.providers import (
    DeterministicEmbeddingProvider,
    DimensionMismatchError,
    EmbeddingFactory,
    EmbeddingProviderError,
    ModelNotAllowedError,
    OllamaEmbeddingProvider,
    OpenAIEmbeddingProvider,
    embedding_production_gate,
    provider_index_identity,
    reindex_required,
    validate_dimensions,
    validate_model,
)
from secondbrain.rag.providers.ollama_http_client import OllamaEmbeddingError
from secondbrain.rag.providers.openai_http_client import OpenAIEmbeddingError


class _OkClient:
    """Returns fixed-dimension vectors for every input text."""

    def __init__(self, dim: int = 3) -> None:
        self.dim = dim

    def embed(self, texts, model):  # noqa: ANN001
        return [[0.1] * self.dim for _ in texts]


class _OfflineOpenAIClient:
    def embed(self, texts, model):  # noqa: ANN001
        raise OpenAIEmbeddingError("OpenAI unavailable: connection refused")


class _OfflineOllamaClient:
    def embed(self, texts, model):  # noqa: ANN001
        raise OllamaEmbeddingError("Ollama unavailable: connection refused")


class _WrongDimClient:
    def embed(self, texts, model):  # noqa: ANN001
        return [[0.1, 0.2] for _ in texts]  # 2 dims


# --- deterministic / DEV_ONLY --------------------------------------------------

def test_deterministic_reports_dev_only_and_not_production_ready():
    provider = DeterministicEmbeddingProvider(dimensions=8)
    report = provider.health()
    assert report.status == "PASS"
    assert report.dev_only is True
    assert report.production_ready is False
    assert report.semantic is False


def test_production_gate_blocks_deterministic():
    provider = DeterministicEmbeddingProvider(dimensions=8)
    verdict = embedding_production_gate(provider, environment="production")
    assert verdict["status"] == "FAIL"
    assert "dev_only_provider_blocked_in_production" in verdict["reasons"]


def test_production_gate_allows_deterministic_in_dev_environment():
    provider = DeterministicEmbeddingProvider(dimensions=8)
    verdict = embedding_production_gate(provider, environment="development")
    assert verdict["status"] == "PASS"


# --- factory fail-closed -------------------------------------------------------

def test_factory_refuses_silent_default_provider():
    with pytest.raises(EmbeddingProviderError):
        EmbeddingFactory.create()


def test_factory_blocks_deterministic_in_production():
    with pytest.raises(EmbeddingProviderError):
        EmbeddingFactory.create("deterministic", {"dimensions": 8}, production=True)


def test_factory_allows_deterministic_in_production_with_explicit_optin():
    provider = EmbeddingFactory.create(
        "deterministic", {"dimensions": 8}, production=True, allow_dev_only=True
    )
    assert isinstance(provider, DeterministicEmbeddingProvider)


def test_factory_allows_deterministic_in_dev_by_default():
    provider = EmbeddingFactory.create("deterministic", {"dimensions": 8})
    assert isinstance(provider, DeterministicEmbeddingProvider)


def test_factory_env_flag_enables_dev_only(monkeypatch):
    provider = EmbeddingFactory.create(
        "local", {"dimensions": 8}, production=True, env={"SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK": "1"}
    )
    assert isinstance(provider, DeterministicEmbeddingProvider)


# --- OpenAI / Ollama offline: FAIL, never silent fallback ----------------------

def test_openai_offline_health_fails_without_fallback():
    provider = OpenAIEmbeddingProvider(model="text-embedding-3-small", client=_OfflineOpenAIClient())
    report = provider.health()
    assert report.status == "FAIL"
    assert report.production_ready is False
    with pytest.raises(OpenAIEmbeddingError):
        provider.embed(["x"])


def test_ollama_offline_health_fails_without_fallback():
    provider = OllamaEmbeddingProvider(model="nomic-embed-text", client=_OfflineOllamaClient())
    report = provider.health()
    assert report.status == "FAIL"
    with pytest.raises(OllamaEmbeddingError):
        provider.embed(["x"])


def test_openai_healthy_passes_production_gate():
    provider = OpenAIEmbeddingProvider(model="m", client=_OkClient(dim=4))
    verdict = embedding_production_gate(provider, environment="production")
    assert verdict["status"] == "PASS"
    assert verdict["index_identity"] == "openai:m:0"


# --- dimension validation ------------------------------------------------------

def test_dimension_mismatch_is_detected_on_embed():
    provider = OpenAIEmbeddingProvider(
        model="m", client=_WrongDimClient(), dimensions=4, enforce_dimensions=True
    )
    with pytest.raises(DimensionMismatchError):
        provider.embed(["x"])


def test_validate_dimensions_helper():
    with pytest.raises(DimensionMismatchError):
        validate_dimensions([[1.0, 2.0, 3.0]], expected=4)
    validate_dimensions([[1.0, 2.0, 3.0, 4.0]], expected=4)


# --- model validation ----------------------------------------------------------

def test_validate_model_rejects_disallowed_model():
    with pytest.raises(ModelNotAllowedError):
        validate_model("text-embedding-3-large", ["text-embedding-3-small"])
    validate_model("text-embedding-3-small", ["text-embedding-3-small"])


# --- reindex on provider-identity change ---------------------------------------

def test_provider_index_identity_and_reindex_flag():
    old = OpenAIEmbeddingProvider(model="text-embedding-3-small", client=_OkClient())
    new = OpenAIEmbeddingProvider(model="text-embedding-3-large", client=_OkClient())
    old_id = provider_index_identity(old)
    new_id = provider_index_identity(new)
    assert old_id != new_id
    assert reindex_required(new_id, old_id) is True
    assert reindex_required(old_id, old_id) is False
    assert reindex_required(old_id, None) is True


# --- unknown provider ----------------------------------------------------------

def test_gate_fails_for_provider_without_health_probe():
    class _Bare:
        name = "mystery"
        model = "x"
        dimensions = 0

    verdict = embedding_production_gate(_Bare(), environment="production")
    assert verdict["status"] == "FAIL"
    assert any("health_probe_failed" in r for r in verdict["reasons"])
