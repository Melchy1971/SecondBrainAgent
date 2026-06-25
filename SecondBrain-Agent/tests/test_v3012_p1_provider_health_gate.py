from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p1_provider_health import evaluate_embedding_provider_health
from secondbrain.p1_production_gate import production_gate_with_golden
from secondbrain.p1_rag_runtime import P1RagRuntime


def test_provider_health_blocks_local_embeddings_for_production(tmp_path):
    rt = P1RagRuntime(tmp_path)

    payload = evaluate_embedding_provider_health(rt, production=True, write_report=True)

    assert payload["schema"] == "secondbrain.p1_provider_health.v1"
    assert payload["ok"] is False
    assert "local_deterministic_embeddings_not_allowed_for_production" in payload["blockers"]
    assert (tmp_path / "runtime" / "reports" / "p1_provider_health_latest.json").exists()


def test_provider_health_launcher_command_registered_and_blocks(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p1-provider-health", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 1
    assert "secondbrain.p1_provider_health.v1" in captured
    assert "embedding_provider_not_production_ready" in captured


def test_module_registry_knows_provider_health_command():
    index = ModuleRegistry().command_index()

    assert index["p1-provider-health"] == "core"
    assert ModuleRegistry().resolve_command("p1-provider-health").key == "core"


def test_production_gate_contains_provider_health_blocker(tmp_path):
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen Memory Evidenz lokale Quellen", source="unit", title="Seed")

    payload = production_gate_with_golden(rt, tmp_path)

    assert payload["ok"] is False
    assert payload["provider_health"]["ok"] is False
    assert any(check["name"] == "embedding_provider_production_ready" and check["ok"] is False for check in payload["checks"])


def test_config_golden_dataset_path_is_used(tmp_path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "golden_retrieval.json").write_text(
        json.dumps(
            {
                "dataset_id": "path_contract",
                "queries": [
                    {
                        "query": "Jarvis Quellen",
                        "expected_terms": ["jarvis", "quellen"],
                        "min_recall_at_k": 0.5,
                        "min_mrr": 0.25,
                        "min_ndcg": 0.25,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rt = P1RagRuntime(tmp_path)
    rt.ingest_text("Jarvis RAG Quellen", source="unit", title="Seed")

    from secondbrain.p1_golden_retrieval import evaluate_golden_retrieval

    payload = evaluate_golden_retrieval(rt, tmp_path)

    assert payload["dataset"]["dataset_id"] == "path_contract"
    assert payload["dataset"]["source"] == "config"
