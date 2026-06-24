from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_golden_retrieval import evaluate_golden_retrieval, load_golden_dataset
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_builtin_golden_dataset_loads_when_no_config_exists(tmp_path):
    dataset = load_golden_dataset(tmp_path)

    assert dataset["ok"] is True
    assert dataset["source"] == "builtin"
    assert dataset["dataset_id"] == "builtin_v1"
    assert len(dataset["queries"]) >= 3


def test_invalid_golden_dataset_blocks(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "golden_retrieval.json").write_text('{"queries": [', encoding="utf-8")

    dataset = load_golden_dataset(tmp_path)

    assert dataset["ok"] is False
    assert dataset["source"] == "config"
    assert dataset["error"]


def test_golden_retrieval_passes_for_seeded_index(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text(
        "Jarvis RAG Quellen. Memory Evidenz. Lokale Quellen fuer SecondBrain Retrieval.",
        source="unit://golden",
        title="Golden Fixture",
    )

    result = evaluate_golden_retrieval(rt, tmp_path, write_report=True)

    assert result["schema"] == "secondbrain.p1_golden_retrieval.v1"
    assert result["ok"] is True
    assert result["status"] == "pass"
    assert result["query_count"] >= 3
    assert result["pass_rate"] == 1.0
    assert (tmp_path / "runtime" / "reports" / "p1_golden_retrieval_latest.json").exists()


def test_custom_golden_dataset_can_block_on_threshold(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "golden_retrieval.json").write_text(
        json.dumps(
            {
                "dataset_id": "strict_test",
                "queries": [
                    {
                        "query": "nicht vorhandene frage",
                        "expected_terms": ["unauffindbar"],
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

    result = evaluate_golden_retrieval(rt, tmp_path)

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["blockers"] == 1
    assert result["dataset"]["dataset_id"] == "strict_test"


def test_p1_golden_eval_launcher_command(tmp_path, capsys):
    assert main(["--project-root", str(tmp_path), "p1-rag-ingest-text", "Jarvis RAG Quellen Memory Evidenz lokale Quellen", "--source", "unit", "--title", "Golden"]) == 0
    assert main(["--project-root", str(tmp_path), "p1-golden-eval", "--write-report"]) == 0
    captured = capsys.readouterr().out

    assert "secondbrain.p1_golden_retrieval.v1" in captured
    assert (tmp_path / "runtime" / "reports" / "p1_golden_retrieval_latest.json").exists()


def test_p1_golden_eval_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p1-golden-eval"] == "core"
    assert ModuleRegistry().resolve_command("p1-golden-eval").key == "core"
