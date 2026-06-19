
from pathlib import Path

from secondbrain.advanced_rag_v109 import AdvancedRagIndex, tokenize, chunk_text, quality_score
from secondbrain.launcher_runtime_v108 import SecondBrainLauncher


def test_tokenize_removes_stopwords():
    tokens = tokenize("Das ist der Projektplan für Connector Runtime und Knowledge Graph")
    assert "projektplan" in tokens
    assert "connector" in tokens
    assert "das" not in tokens


def test_chunk_text_splits_large_markdown():
    text = "# Header\n" + ("Connector Runtime braucht Events. " * 120)
    chunks = chunk_text(text, max_chars=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 520 for c in chunks)


def test_quality_score_bounds():
    score = quality_score("# Plan\n\n- Punkt eins\n- Punkt zwei\n" + "Wissen " * 80)
    assert 0.0 <= score <= 1.0
    assert score > 0.5


def test_advanced_rag_build_search_answer(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Projektplan.md").write_text("# Jarvis Projektplan\n\nConnector Runtime, Event Bus und Agent Kernel bilden die Basis.", encoding="utf-8")
    (vault / "Tischtennis.md").write_text("# Training\n\nTopspin, Block und Rückschlagtraining.", encoding="utf-8")

    rag = AdvancedRagIndex(vault)
    build = rag.build()
    hits = rag.search("Connector Agent Kernel", limit=3)
    answer = rag.answer("Connector Agent Kernel")

    assert build["documents"] == 2
    assert build["chunks"] >= 2
    assert hits[0].path == "Projektplan.md"
    assert "Projektplan" in answer.answer
    assert answer.citations


def test_launcher_rag_commands(tmp_path):
    root = tmp_path / "SecondBrain-Agent"
    (root / "config").mkdir(parents=True)
    (root / "vault").mkdir()
    (root / "vault" / "SecondBrain.md").write_text("# SecondBrain\n\nAdvanced RAG findet lokale Quellen mit Zitaten.", encoding="utf-8")
    (root / "config" / "runtime.yaml").write_text("""
runtime:
  profile: test
  paths:
    vault: vault
    runtime: runtime
    events: events/runtime
  services:
    connectors: false
    advanced_rag: true
""", encoding="utf-8")
    (root / "config" / "ai_runtime_v105.yaml").write_text("""
ai_runtime:
  default_provider: echo
  ollama_enabled: false
""", encoding="utf-8")
    (root / "config" / "connectors_v104.json").write_text('{"connectors": []}', encoding="utf-8")

    launcher = SecondBrainLauncher(root)
    build = launcher.rag_index()
    hits = launcher.rag_search("lokale Quellen", 5)
    answer = launcher.rag_answer("lokale Quellen", 5)

    assert build["chunks"] == 1
    assert hits
    assert answer["citations"]
