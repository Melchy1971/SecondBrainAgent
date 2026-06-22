from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_p1_validate_index_and_quality_report(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text(
        "Jarvis beantwortet nur mit lokalen Quellen. Ohne Evidenz muss der RAG-Core explizit no_evidence liefern.",
        source="unit://quality",
        title="Quality Policy",
    )
    validation = rt.validate_index(write_report=True)
    assert validation["ok"] is True
    assert validation["schema"] == "secondbrain.p1_rag.validation.v1"
    assert (tmp_path / "runtime" / "reports" / "p1_rag_validation_latest.json").exists()
    quality = rt.quality_report("lokalen Quellen Evidenz", write_report=True)
    assert quality["ok"] is True
    assert quality["schema"] == "secondbrain.p1_rag.quality.v1"
    assert any(c["name"] == "no_evidence_is_explicit" for c in quality["checks"])
    assert (tmp_path / "runtime" / "reports" / "p1_rag_quality_latest.json").exists()


def test_p1_launcher_validation_quality_and_gate_v3(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Qualität Quellen", "--source", "unit", "--title", "V182"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-rag-validate", "--write-report"]) == 0
    captured = capsys.readouterr().out
    assert '"schema": "secondbrain.p1_rag.validation.v1"' in captured
    assert main(["--project-root", str(tmp_path), "p1-rag-quality", "RAG Qualität", "--write-report"]) == 0
    captured = capsys.readouterr().out
    assert '"schema": "secondbrain.p1_rag.quality.v1"' in captured
    assert main(["--project-root", str(tmp_path), "p1-gate", "--write-report"]) == 0
    captured = capsys.readouterr().out
    assert '"schema": "secondbrain.p1_gate.v3"' in captured
    report = tmp_path / "runtime" / "reports" / "p1_gate_latest.json"
    assert json.loads(report.read_text(encoding="utf-8"))["quality"]["ok"] is True


def test_p1_v182_commands_registered():
    index = ModuleRegistry().command_index()
    assert index["p1-rag-validate"] == "core"
    assert index["p1-rag-quality"] == "core"
