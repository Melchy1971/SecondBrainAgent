from __future__ import annotations

import json
from pathlib import Path

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime, chunk_text, tokenize


def test_p1_tokenize_and_chunk_are_deterministic():
    assert tokenize("Hallo Jarvis, RAG-Test 2026!") == ["hallo", "jarvis", "rag-test", "2026"]
    chunks = chunk_text("A" * 2000, chunk_size=500, overlap=50)
    assert len(chunks) >= 4
    assert all(chunks)


def test_p1_rag_ingest_search_answer(tmp_path):
    rt = P1RagRuntime(tmp_path)
    ingest = rt.ingest_text("Jarvis nutzt lokale Quellen. RAG liefert Antworten mit Zitaten. PostgreSQL folgt später.", source="unit", title="P1 Plan")
    assert ingest["ok"] is True
    assert ingest["chunks"] == 1
    search = rt.search("RAG Zitaten")
    assert search["ok"] is True
    assert search["hit_count"] >= 1
    assert search["hits"][0]["document_id"] == ingest["document_id"]
    answer = rt.answer("Welche Quellen nutzt Jarvis?")
    assert answer["ok"] is True
    assert answer["citations"]
    assert answer["confidence"] > 0


def test_p1_launcher_commands_roundtrip(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis Memory RAG produktiv", "--source", "test", "--title", "Smoke"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "document_id" in captured
    rc = main(["--project-root", str(tmp_path), "p1-rag-search", "Memory"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "hit_count" in captured
    rc = main(["--project-root", str(tmp_path), "p1-rag-answer", "Memory"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert "citations" in captured


def test_p1_gate_writes_report(tmp_path, capsys):
    main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Gate Probe Content"])
    rc = main(["--project-root", str(tmp_path), "p1-gate", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"schema": "secondbrain.p1_gate.v3"' in captured
    report = tmp_path / "runtime" / "reports" / "p1_gate_latest.json"
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "pass"


def test_p1_command_index_registered():
    index = ModuleRegistry().command_index()
    assert index["p1-rag-status"] == "core"
    assert index["p1-rag-answer"] == "core"
    assert index["p1-gate"] == "core"
