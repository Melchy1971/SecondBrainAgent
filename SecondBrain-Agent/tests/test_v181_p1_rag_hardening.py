from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime, summarize_text, validate_source


def test_p1_source_validation_and_summary_are_deterministic():
    assert validate_source("manual")["ok"] is True
    assert validate_source("")["ok"] is False
    text = "A. " + ("B" * 600)
    assert summarize_text(text, 20).endswith("…")


def test_p1_sources_and_explainability(tmp_path):
    rt = P1RagRuntime(tmp_path)
    ingest = rt.ingest_text(
        "Jarvis indexiert Quellen mit Metadaten. Explain zeigt Treffer, Scores und Zeichenbereiche.",
        source="unit://explain",
        title="Explainability",
        metadata={"kind": "test"},
    )
    assert ingest["ok"] is True
    sources = rt.sources()
    assert sources["documents"] == 1
    assert sources["sources"][0]["metadata"]["kind"] == "test"
    explain = rt.explain("Scores Zeichenbereiche")
    assert explain["ok"] is True
    assert explain["ranking_model"] == "deterministic_tfidf_logtf_length_norm_v1"
    assert explain["hits"][0]["char_range"][1] >= explain["hits"][0]["char_range"][0]


def test_p1_launcher_sources_explain_and_gate_v2(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis P1 Quellen Inventar Explain", "--source", "test", "--title", "V181"])
    assert rc == 0
    rc = main(["--project-root", str(tmp_path), "p1-rag-sources"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"sources"' in captured
    rc = main(["--project-root", str(tmp_path), "p1-rag-explain", "Quellen Explain"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"ranking_model"' in captured
    rc = main(["--project-root", str(tmp_path), "p1-gate", "--write-report"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert '"schema": "secondbrain.p1_gate.v3"' in captured
    report = tmp_path / "runtime" / "reports" / "p1_gate_latest.json"
    assert json.loads(report.read_text(encoding="utf-8"))["schema"] == "secondbrain.p1_gate.v3"


def test_p1_new_commands_registered():
    index = ModuleRegistry().command_index()
    assert index["p1-rag-sources"] == "core"
    assert index["p1-rag-explain"] == "core"
