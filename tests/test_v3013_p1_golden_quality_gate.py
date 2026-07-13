from __future__ import annotations

import json

from launcher import main
from secondbrain.p1_golden_retrieval import evaluate_golden_retrieval
from secondbrain.p1_production_gate import production_gate_with_golden
from secondbrain.p1_rag_runtime import P1RagRuntime


def _write_dataset(root, query="Jarvis Quellen", *, expected_sources=None, min_hit_count=1):
    cfg = root / "config"
    cfg.mkdir()
    (cfg / "golden_retrieval.json").write_text(
        json.dumps(
            {
                "dataset_id": "quality_contract",
                "quality_policy": {"min_pass_rate": 1.0},
                "queries": [
                    {
                        "query": query,
                        "expected_terms": ["jarvis", "quellen"],
                        "expected_sources": expected_sources or [],
                        "min_recall_at_k": 1.0,
                        "min_mrr": 1.0,
                        "min_ndcg": 1.0,
                        "min_hit_count": min_hit_count,
                        "k": 5,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_golden_quality_gate_separates_technical_and_quality_failure(tmp_path):
    _write_dataset(tmp_path, min_hit_count=2)
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="Seed")

    payload = evaluate_golden_retrieval(rt, tmp_path)

    assert payload["schema"] == "secondbrain.p1_golden_retrieval.v2"
    assert payload["technical_ok"] is True
    assert payload["quality_ok"] is False
    assert payload["ok"] is False
    assert payload["results"][0]["failure_reasons"] == ["min_hit_count_not_met"]


def test_golden_quality_gate_validates_expected_lineage(tmp_path):
    _write_dataset(tmp_path, expected_sources=["trusted-source"])
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="other-source", title="Seed")

    payload = evaluate_golden_retrieval(rt, tmp_path)

    assert payload["technical_ok"] is True
    assert payload["quality_ok"] is False
    assert "expected_lineage_not_found" in payload["results"][0]["failure_reasons"]
    assert payload["results"][0]["lineage"]["lineage_ok"] is False


def test_golden_quality_gate_passes_with_terms_and_lineage(tmp_path):
    _write_dataset(tmp_path, expected_sources=["trusted-source"])
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="trusted-source", title="Seed")

    payload = evaluate_golden_retrieval(rt, tmp_path, write_report=True)

    assert payload["ok"] is True
    assert payload["technical_ok"] is True
    assert payload["quality_ok"] is True
    assert payload["pass_rate"] == 1.0
    assert (tmp_path / "runtime" / "reports" / "p1_golden_retrieval_latest.json").exists()


def test_production_gate_exposes_golden_quality_metrics(tmp_path):
    _write_dataset(tmp_path, expected_sources=["trusted-source"])
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="trusted-source", title="Seed")

    payload = production_gate_with_golden(rt, tmp_path)
    golden_check = next(check for check in payload["checks"] if check["name"] == "golden_retrieval_eval_passes")

    assert payload["schema"] == "secondbrain.p1_production.golden.v2"
    assert golden_check["detail"]["quality_ok"] is True
    assert golden_check["detail"]["technical_ok"] is True
    assert "avg_mrr" in golden_check["detail"]


def test_launcher_golden_eval_returns_blocked_for_quality_failure(tmp_path, capsys):
    _write_dataset(tmp_path, min_hit_count=2)
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="Seed")

    rc = main(["--project-root", str(tmp_path), "p1-golden-eval"])
    captured = capsys.readouterr().out

    assert rc == 1
    assert "min_hit_count_not_met" in captured
