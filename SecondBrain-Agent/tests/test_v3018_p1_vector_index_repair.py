from pathlib import Path

from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p1_vector_provider_guard import audit_vector_provider, repair_vector_index
from launcher import main
from secondbrain.module_registry import ModuleRegistry


def test_vector_audit_uses_full_index_identity(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "32")
    runtime = P1RagRuntime(project_root=tmp_path)
    runtime.ingest_text("Jarvis vector identity audit", source="unit", title="Unit")

    audit = audit_vector_provider(runtime)

    assert audit["ok"] is True
    assert audit["current_provider"] == "local-deterministic:default:32"
    assert audit["stale_vectors"] == 0
    assert "stale_vector_provider" not in audit["blockers"]


def test_vector_index_repair_reindexes_after_dimension_change(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "32")
    runtime_32 = P1RagRuntime(project_root=tmp_path)
    runtime_32.ingest_text("Jarvis vector repair after model dimension drift", source="unit", title="Unit")

    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "48")
    runtime_48 = P1RagRuntime(project_root=tmp_path)
    before = audit_vector_provider(runtime_48)
    assert before["ok"] is False
    assert "stale_vector_provider" in before["blockers"]
    assert "dimension_mismatch_vectors" in before["blockers"]

    repaired = repair_vector_index(runtime_48)

    assert repaired["ok"] is True
    assert repaired["action"] == "reindex_current_provider"
    assert repaired["after"]["ok"] is True
    assert repaired["after"]["current_provider"] == "local-deterministic:default:48"
    assert repaired["after"]["stale_vectors"] == 0
    assert repaired["after"]["dimension_mismatch_vectors"] == 0


def test_vector_index_repair_launcher_and_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "32")
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis launcher repair", "--source", "unit"]) == 0

    monkeypatch.setenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "40")
    assert main(["--project-root", str(tmp_path), "p1-vector-index-repair", "--write-report"]) == 0
    assert (Path(tmp_path) / "runtime" / "reports" / "p1_vector_index_repair_latest.json").exists()
    assert ModuleRegistry().resolve_command("p1-vector-index-repair").key == "core"
