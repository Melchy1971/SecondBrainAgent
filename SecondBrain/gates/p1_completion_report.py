"""P1 v19.6 - P1 completion report."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass(frozen=True)
class P1CompletionReport:
    status: str
    maturity: str
    completed_capabilities: list[str]
    remaining_limitations: list[str]
    next_phase: str


def build_p1_completion_report() -> P1CompletionReport:
    return P1CompletionReport(
        status="PASS",
        maturity="P1_RELEASE_CANDIDATE",
        completed_capabilities=[
            "rag_ingestion_foundation",
            "chunk_metadata",
            "source_inventory",
            "query_rewriting",
            "hybrid_retrieval_v2",
            "rrf_fusion",
            "retrieval_kpis",
            "kpi_store",
            "drift_detection",
            "evidence_policy",
            "grounded_answer_composer",
            "e2e_benchmark_suite",
            "p1_production_gate",
            "p1_maturity_gate",
        ],
        remaining_limitations=[
            "external_embedding_providers_require_environment_configuration",
            "pgvector_repository_requires_live_database_migration",
            "llm_generation_intentionally_not_part_of_p1",
            "agent_tool_orchestration_moves_to_p2_or_p3_scope",
        ],
        next_phase="P3_MEMORY_SYSTEM",
    )


def write_p1_completion_report(path: str | Path = "runtime/reports/p1_completion_report.json") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(build_p1_completion_report()), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target
