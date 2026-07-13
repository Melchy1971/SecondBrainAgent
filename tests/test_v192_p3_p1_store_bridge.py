from __future__ import annotations

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_p1_store_bridge import export_p1_sqlite_records, mirror_p1_sqlite_to_store, mirror_project_p1_to_selected_store
from secondbrain.p3_rag_store import SQLiteRagStore


def test_export_p1_sqlite_records_empty_when_db_missing(tmp_path):
    payload = export_p1_sqlite_records(tmp_path / "missing.sqlite3")

    assert payload["schema"] == "secondbrain.p3_p1_store_bridge.v1"
    assert payload["ok"] is True
    assert payload["status"] == "empty"
    assert payload["documents"] == []
    assert payload["chunks"] == []
    assert payload["vectors"] == []


def test_export_p1_sqlite_records_from_runtime(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Bridge")

    payload = export_p1_sqlite_records(rt.db_path)

    assert payload["ok"] is True
    assert payload["status"] == "pass"
    assert len(payload["documents"]) == 1
    assert len(payload["chunks"]) >= 1
    assert len(payload["vectors"]) >= 1
    assert payload["documents"][0].title == "Bridge"
    assert payload["chunks"][0].document_id == payload["documents"][0].id
    assert payload["vectors"][0].provider.startswith("local-deterministic:")


def test_mirror_p1_sqlite_to_separate_sqlite_store(tmp_path):
    source_root = tmp_path / "source"
    target_db = tmp_path / "target" / "rag.sqlite3"
    rt = P1RagRuntime(source_root)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Mirror")
    target_store = SQLiteRagStore(target_db)

    payload = mirror_p1_sqlite_to_store(rt.db_path, target_store)

    assert payload["ok"] is True
    assert payload["target_backend"] == "sqlite"
    assert payload["documents"] == 1
    assert payload["chunks"] >= 1
    assert payload["vectors"] >= 1
    assert target_store.status()["documents"] == 1
    assert target_store.sources()["sources"][0]["title"] == "Mirror"


def test_project_bridge_noops_when_selected_store_is_existing_sqlite(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="Noop")

    payload = mirror_project_p1_to_selected_store(tmp_path, write_report=True)

    assert payload["ok"] is True
    assert payload["status"] == "noop"
    assert payload["target_backend"] == "sqlite"
    assert payload["store_status"]["documents"] == 1
    assert (tmp_path / "runtime" / "reports" / "p3_p1_store_bridge_latest.json").exists()


def test_p3_p1_store_bridge_launcher_command(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen", "--source", "unit", "--title", "BridgeCLI"]) == 0
    assert main(["--project-root", str(tmp_path), "p3-p1-store-bridge", "--write-report"]) == 0
    captured = capsys.readouterr().out

    assert "secondbrain.p3_p1_store_bridge.v1" in captured
    assert '"status": "noop"' in captured
    assert (tmp_path / "runtime" / "reports" / "p3_p1_store_bridge_latest.json").exists()


def test_p3_p1_store_bridge_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p3-p1-store-bridge"] == "core"
    assert ModuleRegistry().resolve_command("p3-p1-store-bridge").key == "core"
