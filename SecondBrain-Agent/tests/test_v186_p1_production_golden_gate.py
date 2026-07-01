from __future__ import annotations

import json

from launcher import main
from secondbrain.p1_production_gate import production_gate_with_golden
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_production_gate_wrapper_includes_golden_retrieval(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text(
        "Jarvis RAG Quellen Memory Evidenz lokale Quellen",
        source="unit://production-golden",
        title="Production Golden",
    )

    payload = production_gate_with_golden(rt, tmp_path, write_report=True)

    assert payload["schema"].startswith("secondbrain.p1_production.golden.v")
    assert "base_production" in payload
    assert "golden_retrieval" in payload
    assert payload["golden_retrieval"]["ok"] is True
    assert any(check["name"] == "golden_retrieval_eval_passes" for check in payload["checks"])
    assert (tmp_path / "runtime" / "reports" / "p1_production_latest.json").exists()


def test_production_gate_wrapper_fails_when_golden_dataset_fails(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "golden_retrieval.json").write_text(
        json.dumps(
            {
                "dataset_id": "strict_eval",
                "queries": [
                    {
                        "query": "absent evaluation phrase",
                        "expected_terms": ["missingterm"],
                        "min_recall_at_k": 1.0,
                        "min_mrr": 1.0,
                        "min_ndcg": 1.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="Seed")

    payload = production_gate_with_golden(rt, tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "blocked"
    assert any(check["name"] == "golden_retrieval_eval_passes" and check["ok"] is False for check in payload["checks"])


def test_p1_production_launcher_uses_golden_wrapper(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen Memory Evidenz lokale Quellen", "--source", "unit", "--title", "Golden"]) == 0
    rc = main(["--project-root", str(tmp_path), "p1-production", "--write-report"])
    captured = capsys.readouterr().out

    # Local deterministic embeddings still prevent production PASS, but the
    # payload must now include the Golden Retrieval layer.
    assert rc == 1
    assert "secondbrain.p1_production.golden.v" in captured
    assert "golden_retrieval_eval_passes" in captured
    assert (tmp_path / "runtime" / "reports" / "p1_production_latest.json").exists()
