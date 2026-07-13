from pathlib import Path

from secondbrain.p1_embeddings import LocalEmbeddingProvider, embedding_index_provider
from secondbrain.p1_provider_health import evaluate_embedding_provider_health
from secondbrain.p1_rag_runtime import P1RagRuntime


class RuntimeStub:
    def __init__(self, provider, reports_dir):
        self.embedding_provider = provider
        self.reports_dir = Path(reports_dir)


def test_local_embedding_index_identity_includes_dimension():
    provider = LocalEmbeddingProvider(dimensions=128)
    assert embedding_index_provider(provider) == "local-deterministic:default:128"
    assert provider.status()["index_provider"] == "local-deterministic:default:128"


def test_provider_health_reports_index_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    provider = LocalEmbeddingProvider(dimensions=64)
    result = evaluate_embedding_provider_health(RuntimeStub(provider, tmp_path / "runtime" / "reports"), production=False)
    assert result["index_provider"] == "local-deterministic:default:64"
    assert "embedding_index_provider_missing" not in result["blockers"]


def test_runtime_stores_vectors_under_index_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "32")
    runtime = P1RagRuntime(project_root=tmp_path)
    result = runtime.ingest_text("Jarvis memory source evidence", source="unit", title="Unit")
    assert result["ok"] is True
    summary = runtime.embedding_status()
    providers = summary["indexed_vectors"]
    assert providers
    assert providers[0]["provider"] == "local-deterministic:default:32"


def test_vector_search_filters_current_index_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "32")
    runtime = P1RagRuntime(project_root=tmp_path)
    runtime.ingest_text("Jarvis retrieval identity guard", source="unit", title="Unit")
    search = runtime.vector_search("Jarvis retrieval", limit=3)
    assert search["ok"] is True
    assert search["hits"]
    assert search["hits"][0]["provider"] == "local-deterministic:default:32"
