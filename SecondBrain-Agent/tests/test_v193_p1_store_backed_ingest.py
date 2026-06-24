from __future__ import annotations

from launcher import main
from secondbrain.p1_rag_runtime import P1RagRuntime
from secondbrain.p3_rag_store import SQLiteRagStore


def test_p1_ingest_text_writes_through_rag_store(tmp_path):
    rt = P1RagRuntime(tmp_path)

    result = rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="StoreBacked")

    assert result["ok"] is True
    assert result["store"]["backend"] == "sqlite"
    assert result["store"]["write_path"] == "rag_store"
    assert result["store"]["document"]["ok"] is True
    assert result["store"]["chunks"]["chunks"] == result["chunks"]
    assert result["store"]["vectors"]["vectors"] == result["chunks"]

    store = SQLiteRagStore(rt.db_path)
    status = store.status()
    assert status["documents"] == 1
    assert status["chunks"] == result["chunks"]
    assert status["vectors"] == result["chunks"]


def test_p1_store_backed_ingest_keeps_existing_search_working(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Search")

    keyword = rt.search("Jarvis Quellen")
    vector = rt.vector_search("Jarvis Quellen")
    hybrid = rt.hybrid_search("Jarvis Quellen")

    assert keyword["hit_count"] >= 1
    assert vector["hit_count"] >= 1
    assert hybrid["hit_count"] >= 1


def test_p1_reindex_vectors_writes_through_rag_store(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Reindex")

    result = rt.reindex_vectors(write_report=True)

    assert result["ok"] is True
    assert result["store"]["backend"] == "sqlite"
    assert result["store"]["write_path"] == "rag_store"
    assert result["store"]["vectors"]["vectors"] == result["chunks"]
    assert (tmp_path / "runtime" / "reports" / "p1_vector_reindex_latest.json").exists()


def test_p1_store_backed_ingest_launcher_smoke(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen", "--source", "unit", "--title", "CLI"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert '"write_path": "rag_store"' in captured
    assert main(["--project-root", str(tmp_path), "p1-rag-search", "Jarvis"]) == 0
