from __future__ import annotations

from datetime import datetime, timedelta, timezone

from secondbrain.chat.context import (
    ConflictResolver,
    ContextBuilder,
    ContextCandidate,
    ContextOptimizer,
    ContextRanker,
    DuplicateRemover,
    PromptCompressor,
    PromptExpander,
    SourceRanker,
    TokenBudgetManager,
)
from secondbrain.chat.context.prompt_assembler import PromptAssembler


def _candidate(identifier: str, text: str, *, section: str = "documents", source: str = "documents",
               score: float = 0.5, metadata=None, created_at=None) -> ContextCandidate:
    return ContextCandidate(identifier, text, section, source, score, created_at, metadata or {})


def test_context_memory_and_source_ranking_are_deterministic() -> None:
    now = datetime.now(timezone.utc)
    candidates = [
        _candidate("old", "unrelated note", section="semantic_memory", source="memory",
                   created_at=now - timedelta(days=100)),
        _candidate("trusted", "Atlas release status", section="semantic_memory", source="memory",
                   metadata={"source_trust": 0.95}, created_at=now),
        _candidate("document", "Atlas release", source="documents", metadata={"source_trust": 0.2}),
    ]

    ranked = ContextRanker().rank(candidates, "Atlas release status")

    assert ranked[0].candidate.id == "trusted"
    assert ranked[0].relevance == 1.0
    assert ranked[0].source_score == 0.95
    assert SourceRanker().score(candidates[0]) == 0.8


def test_duplicate_removal_keeps_highest_ranked_exact_and_near_duplicates() -> None:
    candidates = [
        _candidate("best", "Atlas uses PostgreSQL for durable storage.", score=1.0),
        _candidate("exact", "  atlas uses PostgreSQL for durable storage. ", score=0.5),
        _candidate("near", "Atlas uses PostgreSQL for durable storage", score=0.4),
    ]
    ranked = ContextRanker().rank(candidates, "Atlas PostgreSQL")

    kept, removed = DuplicateRemover(near_duplicate_threshold=0.8).remove(ranked)

    assert [row.candidate.id for row in kept] == ["best"]
    assert set(removed) == {"exact", "near"}


def test_conflict_resolution_reuses_detector_and_keeps_stronger_source() -> None:
    candidates = [
        _candidate("current", "Budget is 20", section="semantic_memory", source="memory",
                   metadata={"claim_key": "budget", "claim_value": 20, "source_trust": 0.95}),
        _candidate("stale", "Budget is 10", section="semantic_memory", source="memory",
                   metadata={"claim_key": "budget", "claim_value": 10, "source_trust": 0.1}),
    ]
    ranked = ContextRanker().rank(candidates, "budget")

    kept, removed, conflicts = ConflictResolver().resolve(ranked)

    assert [row.candidate.id for row in kept] == ["current"]
    assert removed == ["stale"]
    assert conflicts[0]["reason"] == "claim_value_mismatch"
    assert conflicts[0]["winner"] == "current"


def test_context_optimizer_reports_ranking_duplicates_and_conflicts() -> None:
    candidates = [
        _candidate("doc", "Atlas status is green", score=0.9),
        _candidate("copy", "Atlas status is green", score=0.2),
        _candidate("yes", "Deployment is enabled", section="semantic_memory",
                   metadata={"claim_key": "deploy", "claim_value": True, "source_trust": 0.9}),
        _candidate("no", "Deployment is disabled", section="semantic_memory",
                   metadata={"claim_key": "deploy", "claim_value": False, "source_trust": 0.2}),
    ]

    report = ContextOptimizer().optimize("Atlas deployment status", candidates).report()

    assert report["duplicates_removed"] == 1
    assert report["conflicts_removed"] == 1
    assert report["selected"] == 2


def test_context_optimizer_ignores_empty_candidates() -> None:
    result = ContextOptimizer().optimize("Atlas", [_candidate("empty", "   ")])
    assert result.report()["selected"] == 0


def test_prompt_compression_expansion_and_budget() -> None:
    compressor = PromptCompressor()
    compressed = compressor.compress("Status?   Status?   Details follow.", max_tokens=5)
    expanded = PromptExpander().expand(
        "Atlas status",
        context_terms=["release", "release"],
        constraints=["cite sources"],
    )

    assert compressed.startswith("Status? Details")
    assert compressed.count("Status?") == 1
    assert "Relevant context: release" in expanded
    assert "Constraints: cite sources" in expanded
    assert TokenBudgetManager.estimate_tokens(compressed) <= 5


def test_prompt_assembler_expansion_is_explicit_and_backward_compatible() -> None:
    assembler = PromptAssembler()
    plain = assembler.completion_request("  Atlas   status  ", [], "", "m", stream=False)
    optimized = assembler.completion_request(
        "  Atlas   status  ", [], "", "m", stream=False,
        compress_prompt=True, expand_prompt=True,
        context_terms=["release"], constraints=["cite sources"],
    )

    assert plain.messages[-1].content == "  Atlas   status  "
    assert optimized.messages[-1].content.startswith("Atlas status\n")
    assert "release" in optimized.messages[-1].content


class _Memory:
    def search(self, query: str, limit: int = 5):
        return {"memories": [
            {"memory_id": "m1", "content": "Atlas uses PostgreSQL", "source": "memory", "score": 0.8},
            {"memory_id": "m2", "content": "Atlas uses PostgreSQL", "source": "memory", "score": 0.2},
        ]}


class _Rag:
    def hybrid_search(self, query: str, limit: int = 5):
        return {"hits": [
            {"document_id": "d1", "chunk_id": "c1", "text": "Release evidence", "source": "manual", "score": 0.9},
        ]}


def test_existing_context_pipeline_exposes_optimization_and_token_budget(tmp_path) -> None:
    budget = TokenBudgetManager(max_tokens=512, reserved_output_tokens=0)
    result = ContextBuilder(tmp_path, rag_runtime=_Rag(), memory_explorer=_Memory(), budget=budget).build(
        "Atlas release", [], selected_sources=("documents", "memory")
    )

    assert result["optimization"]["duplicates_removed"] == 1
    assert len(result["memories"]) == 1
    assert result["hits"][0]["chunk_id"] == "c1"
    assert result["budget"]["used"] <= result["budget"]["input_budget"]
