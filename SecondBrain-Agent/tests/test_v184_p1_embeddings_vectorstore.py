from __future__ import annotations

import json
import sys
import types

import pytest

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_embeddings import LocalEmbeddingProvider, OpenAIEmbeddingProvider, cosine_similarity
from secondbrain.p1_rag_runtime import P1RagRuntime


class _FakeEmbedding:
    def __init__(self, values):
        self.embedding = values


class _FakeDataResponse:
    def __init__(self, values):
        self.data = [_FakeEmbedding(values)]


class _FakeEmbeddingsApi:
    def create(self, *, model, input):
        assert model
        assert input
        return _FakeDataResponse([1.0, 2.0, 3.0, 4.0])


class _FakeOpenAIClient:
    def __init__(self, *, api_key):
        assert api_key == "test-key"
        self.embeddings = _FakeEmbeddingsApi()


def test_local_embedding_provider_is_deterministic_but_not_production_ready():
    provider = LocalEmbeddingProvider(dimensions=32)
    a = provider.embed("Jarvis lokale Quellen")
    b = provider.embed("Jarvis lokale Quellen")
    c = provider.embed("anderer Inhalt")
    status = provider.status()

    assert a == b
    assert len(a) == 32
    assert cosine_similarity(a, b) > cosine_similarity(a, c)
    assert status["provider"] == "local-deterministic"
    assert status["ok"] is True
    assert status["production_ready"] is False
    assert status["semantic"] is False


def test_openai_embedding_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", raising=False)
    provider = OpenAIEmbeddingProvider()

    status = provider.status()

    assert status["ok"] is False
    assert status["production_ready"] is False
    assert status["fallback_used"] is False
    assert status["fallback_allowed"] is False
    assert status["error"] == "openai_api_key_missing"
    with pytest.raises(RuntimeError, match="openai_embedding_unavailable"):
        provider.embed("must block without api key")


def test_openai_embedding_provider_reports_missing_sdk(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", raising=False)
    monkeypatch.setitem(sys.modules, "openai", None)
    provider = OpenAIEmbeddingProvider()

    status = provider.status()

    assert status["ok"] is False
    assert status["production_ready"] is False
    assert status["fallback_used"] is False
    assert status["fallback_allowed"] is False
    assert status["error"] == "openai_sdk_missing"


def test_openai_embedding_provider_uses_sdk_when_available(monkeypatch):
    fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAIClient)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", fake_module)
    provider = OpenAIEmbeddingProvider(model="fake-embedding-model")

    vector = provider.embed("Jarvis semantic retrieval")
    status = provider.status()

    assert len(vector) == 4
    assert status["ok"] is True
    assert status["provider"] == "openai"
    assert status["model"] == "fake-embedding-model"
    assert status["production_ready"] is True
    assert status["fallback_used"] is False
    assert status["dimensions"] == 4


def test_openai_embedding_provider_blocks_on_sdk_failure_by_default(monkeypatch):
    class BrokenEmbeddingsApi:
        def create(self, *, model, input):
            raise RuntimeError("boom")

    class BrokenClient:
        def __init__(self, *, api_key):
            self.embeddings = BrokenEmbeddingsApi()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", raising=False)
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=BrokenClient))
    provider = OpenAIEmbeddingProvider(dimensions=16)

    with pytest.raises(RuntimeError, match="openai_embedding_unavailable"):
        provider.embed("fallback path")
    status = provider.status()

    assert status["ok"] is False
    assert status["production_ready"] is False
    assert status["fallback_used"] is False
    assert status["fallback_allowed"] is False
    assert "boom" in status["error"]


def test_openai_embedding_provider_fallback_requires_explicit_opt_in(monkeypatch):
    class BrokenEmbeddingsApi:
        def create(self, *, model, input):
            raise RuntimeError("boom")

    class BrokenClient:
        def __init__(self, *, api_key):
            self.embeddings = BrokenEmbeddingsApi()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", "true")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=BrokenClient))
    provider = OpenAIEmbeddingProvider(dimensions=16)

    vector = provider.embed("fallback path")
    status = provider.status()

    assert len(vector) == 16
    assert status["ok"] is False
    assert status["production_ready"] is False
    assert status["fallback_used"] is True
    assert status["fallback_allowed"] is True
    assert "boom" in status["error"]


def test_p1_ingest_creates_vectors_and_hybrid_search(tmp_path):
    rt = P1RagRuntime(tmp_path)
    ingest = rt.ingest_text(
        "Jarvis nutzt lokale Quellen. Der VectorStore speichert Embeddings für Hybrid Retrieval.",
        source="unit://v184",
        title="VectorStore",
    )
    assert ingest["ok"] is True
    embedding_status = rt.embedding_status()
    assert embedding_status["ok"] is True
    assert embedding_status["provider"]["production_ready"] is False
    assert embedding_status["indexed_vectors"][0]["chunks"] == ingest["chunks"]
    vector = rt.vector_search("Embeddings Hybrid", 3)
    assert vector["ok"] is True
    assert vector["hit_count"] >= 1
    hybrid = rt.hybrid_search("lokale Quellen VectorStore", 3)
    assert hybrid["schema"] == "secondbrain.p1_hybrid.search.v1"
    assert hybrid["hit_count"] >= 1
    assert "hybrid_score" in hybrid["hits"][0]


def test_p1_reindex_benchmark_and_gate_v4(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Benchmark")
    reindex = rt.reindex_vectors(write_report=True)
    assert reindex["ok"] is True
    assert (tmp_path / "runtime" / "reports" / "p1_vector_reindex_latest.json").exists()
    benchmark = rt.retrieval_benchmark(write_report=True)
    assert benchmark["schema"] == "secondbrain.p1_retrieval.benchmark.v1"
    assert benchmark["hit_rate"] > 0
    gate = rt.gate(write_report=True)
    assert gate["schema"] == "secondbrain.p1_gate.v4"
    assert gate["ok"] is True
    assert json.loads((tmp_path / "runtime" / "reports" / "p1_gate_latest.json").read_text(encoding="utf-8"))["schema"] == "secondbrain.p1_gate.v4"


def test_p1_production_gate_blocks_local_fallback_embeddings(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Benchmark")

    production = rt.production_gate(write_report=True)

    assert production["schema"] == "secondbrain.p1_production.v1"
    assert production["ok"] is False
    assert production["status"] == "blocked"
    assert any(check["name"] == "embedding_provider_production_ready" and check["ok"] is False for check in production["checks"])
    assert (tmp_path / "runtime" / "reports" / "p1_production_latest.json").exists()


def test_p1_v184_launcher_commands_and_registry(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis Embeddings Hybrid Retrieval", "--source", "unit", "--title", "CLI"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-embedding-status"]) == 0
    assert "secondbrain.p1_embeddings.status.v1" in capsys.readouterr().out
    assert main(["--project-root", str(tmp_path), "p1-rag-hybrid-search", "Hybrid Retrieval"]) == 0
    assert "secondbrain.p1_hybrid.search.v1" in capsys.readouterr().out
    assert main(["--project-root", str(tmp_path), "p1-rag-reindex", "--write-report"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-retrieval-benchmark", "--write-report"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-gate", "--write-report"]) == 0
    assert "secondbrain.p1_gate.v4" in capsys.readouterr().out
    index = ModuleRegistry().command_index()
    assert index["p1-embedding-status"] == "core"
    assert index["p1-rag-hybrid-search"] == "core"
    assert index["p1-retrieval-benchmark"] == "core"
