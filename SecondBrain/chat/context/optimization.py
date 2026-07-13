"""v30.73 deterministic optimization for the existing chat context pipeline."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from secondbrain.agent.memory_injection.conflicts import MemoryConflictDetector
from secondbrain.agent.memory_injection.ranking import MemoryRanking
from secondbrain.chat.context.token_budget import TokenBudgetManager

_WORD = re.compile(r"[\w-]+", re.UNICODE)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _terms(text: str) -> set[str]:
    return {term.casefold() for term in _WORD.findall(text or "")}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class ContextCandidate:
    id: str
    text: str
    section: str
    source: str = ""
    base_score: float = 0.5
    created_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, identifier: str, text: str, section: str, row: Mapping[str, Any]) -> "ContextCandidate":
        metadata = dict(row.get("metadata") or {})
        metadata.update({key: value for key, value in row.items() if key not in {"metadata", "text", "content"}})
        raw_score = row.get("score", row.get("confidence", 0.5))
        try:
            base_score = float(raw_score)
        except (TypeError, ValueError):
            base_score = 0.5
        return cls(
            id=identifier,
            text=str(text),
            section=section,
            source=str(row.get("source") or section),
            base_score=_clamp(base_score),
            created_at=_datetime(row.get("created_at") or row.get("updated_at")),
            metadata=metadata,
        )


@dataclass(frozen=True)
class RankedContext:
    candidate: ContextCandidate
    relevance: float
    memory_score: float
    source_score: float
    score: float


@dataclass(frozen=True)
class OptimizationResult:
    ranked: tuple[RankedContext, ...]
    duplicate_ids: tuple[str, ...]
    conflict_ids: tuple[str, ...]
    conflicts: tuple[dict[str, Any], ...]

    def report(self) -> dict[str, Any]:
        return {
            "selected": len(self.ranked),
            "duplicates_removed": len(self.duplicate_ids),
            "conflicts_removed": len(self.conflict_ids),
            "duplicate_ids": list(self.duplicate_ids),
            "conflict_ids": list(self.conflict_ids),
            "conflicts": list(self.conflicts),
            "ranking": [
                {
                    "id": row.candidate.id,
                    "section": row.candidate.section,
                    "score": round(row.score, 6),
                    "relevance": round(row.relevance, 6),
                    "memory_score": round(row.memory_score, 6),
                    "source_score": round(row.source_score, 6),
                }
                for row in self.ranked
            ],
        }


class SourceRanker:
    """Ranks provenance while honoring explicit trust/confidence metadata."""

    DEFAULT_TRUST = {
        "documents": 0.85,
        "rag": 0.85,
        "semantic_memory": 0.8,
        "memory": 0.8,
        "workspace": 0.8,
        "conversation": 0.75,
        "agents": 0.7,
        "attachments": 0.65,
    }

    def __init__(self, trust: Mapping[str, float] | None = None) -> None:
        self.trust = {**self.DEFAULT_TRUST, **dict(trust or {})}

    def score(self, candidate: ContextCandidate) -> float:
        for key in ("source_trust", "trust", "confidence"):
            value = candidate.metadata.get(key)
            if isinstance(value, (int, float)):
                return _clamp(value)
        return _clamp(self.trust.get(candidate.source, self.trust.get(candidate.section, 0.5)))


@dataclass
class _MemoryRecord:
    memory_id: str
    text: str
    created_at: datetime | None
    metadata: Mapping[str, Any]


class ContextRanker:
    """Fuses query relevance, existing scores, MemoryRanking and source trust."""

    def __init__(self, *, memory_ranking: MemoryRanking | None = None, source_ranking: SourceRanker | None = None) -> None:
        self.memory_ranking = memory_ranking or MemoryRanking()
        self.source_ranking = source_ranking or SourceRanker()

    def rank(self, candidates: Iterable[ContextCandidate], query: str) -> list[RankedContext]:
        pool = list(candidates)
        memory_records = [
            _MemoryRecord(row.id, row.text, row.created_at, row.metadata)
            for row in pool
            if row.section == "semantic_memory"
        ]
        memory_scores = {
            row.record.memory_id: row.score for row in self.memory_ranking.rank(memory_records, query)
        }
        query_terms = _terms(query)
        ranked: list[RankedContext] = []
        for candidate in pool:
            terms = _terms(candidate.text)
            relevance = len(query_terms & terms) / len(query_terms) if query_terms else 1.0
            if query.strip() and query.casefold() in candidate.text.casefold():
                relevance = max(relevance, 0.9)
            memory_score = memory_scores.get(candidate.id, _clamp(candidate.base_score))
            source_score = self.source_ranking.score(candidate)
            score = 0.5 * relevance + 0.3 * memory_score + 0.2 * source_score
            ranked.append(RankedContext(candidate, relevance, memory_score, source_score, _clamp(score)))
        return sorted(ranked, key=lambda row: (-row.score, row.candidate.id))


class DuplicateRemover:
    def __init__(self, *, near_duplicate_threshold: float = 0.92) -> None:
        self.near_duplicate_threshold = _clamp(near_duplicate_threshold)

    def remove(self, ranked: Iterable[RankedContext]) -> tuple[list[RankedContext], list[str]]:
        kept: list[RankedContext] = []
        removed: list[str] = []
        signatures: list[set[str]] = []
        normalized_seen: set[str] = set()
        for row in ranked:
            normalized = " ".join(row.candidate.text.casefold().split())
            terms = _terms(normalized)
            duplicate = normalized in normalized_seen
            if not duplicate and terms:
                duplicate = any(len(terms & other) / len(terms | other) >= self.near_duplicate_threshold for other in signatures)
            if duplicate:
                removed.append(row.candidate.id)
                continue
            kept.append(row)
            normalized_seen.add(normalized)
            signatures.append(terms)
        return kept, removed


class ConflictResolver:
    """Uses the existing detector and retains the highest-ranked assertion."""

    def __init__(self, detector: MemoryConflictDetector | None = None) -> None:
        self.detector = detector or MemoryConflictDetector()

    def resolve(self, ranked: Iterable[RankedContext]) -> tuple[list[RankedContext], list[str], list[dict[str, Any]]]:
        rows = list(ranked)
        memory_rows = [row for row in rows if row.candidate.section == "semantic_memory"]
        records = [
            _MemoryRecord(row.candidate.id, row.candidate.text, row.candidate.created_at, row.candidate.metadata)
            for row in memory_rows
        ]
        conflicts = self.detector.detect(records)
        rank_position = {row.candidate.id: index for index, row in enumerate(rows)}
        removed: set[str] = set()
        details: list[dict[str, Any]] = []
        for conflict in conflicts:
            candidates = [item for item in conflict.memory_ids if item not in removed]
            if len(candidates) < 2:
                continue
            winner = min(candidates, key=lambda item: rank_position.get(item, len(rows)))
            losers = [item for item in candidates if item != winner]
            removed.update(losers)
            details.append({
                "memory_ids": list(conflict.memory_ids),
                "reason": conflict.reason,
                "detail": conflict.detail,
                "winner": winner,
                "removed": losers,
            })
        return [row for row in rows if row.candidate.id not in removed], sorted(removed), details


class PromptCompressor:
    """Lossless whitespace/repetition compression plus optional hard budget."""

    def compress(self, prompt: str, *, max_tokens: int | None = None) -> str:
        sentences: list[str] = []
        seen: set[str] = set()
        for sentence in _SENTENCE.split(" ".join((prompt or "").split())):
            normalized = sentence.casefold()
            if sentence and normalized not in seen:
                sentences.append(sentence)
                seen.add(normalized)
        result = " ".join(sentences)
        if max_tokens is not None:
            if max_tokens < 1:
                raise ValueError("max_tokens must be >= 1")
            char_limit = TokenBudgetManager.estimate_chars(max_tokens)
            result = result[:char_limit].rstrip()
        return result


class PromptExpander:
    """Explicitly enriches a prompt with supplied context terms and constraints."""

    def expand(self, prompt: str, *, context_terms: Iterable[str] = (), constraints: Iterable[str] = ()) -> str:
        base = " ".join((prompt or "").split())
        terms = list(dict.fromkeys(str(item).strip() for item in context_terms if str(item).strip()))
        rules = list(dict.fromkeys(str(item).strip() for item in constraints if str(item).strip()))
        parts = [base]
        if terms:
            parts.append("Relevant context: " + ", ".join(terms))
        if rules:
            parts.append("Constraints: " + "; ".join(rules))
        return "\n".join(part for part in parts if part)


class ContextOptimizer:
    def __init__(self, *, ranker: ContextRanker | None = None, duplicates: DuplicateRemover | None = None,
                 conflicts: ConflictResolver | None = None) -> None:
        self.ranker = ranker or ContextRanker()
        self.duplicates = duplicates or DuplicateRemover()
        self.conflicts = conflicts or ConflictResolver()

    def optimize(self, query: str, candidates: Iterable[ContextCandidate]) -> OptimizationResult:
        ranked = self.ranker.rank((row for row in candidates if row.text.strip()), query)
        unique, duplicate_ids = self.duplicates.remove(ranked)
        resolved, conflict_ids, conflicts = self.conflicts.resolve(unique)
        return OptimizationResult(tuple(resolved), tuple(duplicate_ids), tuple(conflict_ids), tuple(conflicts))
