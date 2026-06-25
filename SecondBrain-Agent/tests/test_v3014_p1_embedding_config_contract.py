from __future__ import annotations

import json

import pytest

from launcher import main
from secondbrain.p1_embedding_config import evaluate_embedding_config, load_embedding_config
from secondbrain.p1_embeddings import LocalEmbeddingProvider, OllamaEmbeddingProvider, OpenAIEmbeddingProvider, provider_from_profile
from secondbrain.p1_provider_health import evaluate_embedding_provider_health
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_default_local_config_is_blocked_for_production(tmp_path):
    payload = evaluate_embedding_config(tmp_path, production=True, write_report=True)

    assert payload["schema"] == "secondbrain.p1_embedding_config.v1"
    assert payload["ok"] is False
    assert "embedding_provider_not_allowed_for_production" in payload["blockers"]
    assert (tmp_path / "runtime" / "reports" / "p1_embedding_config_latest.json").exists()


def test_ollama_config_reads_env_and_builds_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_MODEL", "nomic-embed-text")
    monkeypatch.setenv("SECONDBRAIN_OLLAMA_BASE_URL", "http://ollama.local:11434")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "768")

    cfg = load_embedding_config(tmp_path)
    provider = provider_from_profile(tmp_path)

    assert cfg.provider == "ollama"
    assert cfg.ollama_base_url == "http://ollama.local:11434"
    assert cfg.dimensions == 768
    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.base_url == "http://ollama.local:11434"
    assert provider.dimensions == 768


def test_openai_config_requires_api_key_for_production(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("SECONDBRAIN_OPENAI_API_KEY_ENV", "SB_TEST_OPENAI_KEY")
    monkeypatch.delenv("SB_TEST_OPENAI_KEY", raising=False)

    payload = evaluate_embedding_config(tmp_path, production=True)
    provider = provider_from_profile(tmp_path)

    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.api_key_env == "SB_TEST_OPENAI_KEY"
    assert "openai_api_key_env_not_set" in payload["blockers"]


def test_unknown_embedding_provider_blocks_runtime_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "fake-provider")

    with pytest.raises(ValueError, match="unknown_embedding_provider"):
        provider_from_profile(tmp_path)


def test_embedding_config_launcher_command(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p1-embedding-config", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 1
    assert "secondbrain.p1_embedding_config.v1" in captured
    assert "embedding_provider_not_allowed_for_production" in captured


def test_provider_health_includes_config_health(tmp_path):
    rt = P1RagRuntime(tmp_path)

    payload = evaluate_embedding_provider_health(rt, production=True)

    assert payload["ok"] is False
    assert payload["config_health"]["schema"] == "secondbrain.p1_embedding_config.v1"
    assert "embedding_provider_not_allowed_for_production" in payload["blockers"]
