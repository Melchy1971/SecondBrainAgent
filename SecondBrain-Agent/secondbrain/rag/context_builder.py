"""Context assembly for RAG answer generation.

P1.1.5 turns ranked retrieval results into a bounded, deterministic context
payload. The builder is deliberately dependency-free and conservative: it
removes duplicate text, respects max-chunk and token budgets, keeps result
ordering stable, and preserves source metadata for citations/debugging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterable, Mapping

from secondbrain.rag.retrieval.score_fusion import SearchResult


@dataclass(frozen=True)
class ContextBuilderConfig:
    """Budget controls for RAG context construction."""

    max_chunks: int = 8
    max_tokens: int = 6000
    include_scores: bool = True
    separator: str = "\n\n---\n\n"

    def __post_init__(self) -> None:
        if self.max_chunks < 1:
            raise ValueError("max_chunks must be >= 1")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if not isinstance(self.separator, str):
            raise ValueError("separator must be a string")


@dataclass(frozen=True)
class ContextChunk:
    """A selected chunk included in the final prompt context."""

    document_id: str
    chunk_id: str
    text: str
    score: float
    token_count: int
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BuiltContext:
    """Final context payload plus trace metadata."""

    text: str
    chunks: tuple[ContextChunk, ...]
    total_tokens: int
    skipped_duplicates: int
    skipped_budget: int

    @property
    def is_empty(self) -> bool:
        return not self.chunks


class ContextBuilder:
    """Build a prompt-ready context from ranked retrieval results."""

    def __init__(self, config: ContextBuilderConfig | None = None) -> None:
        self.config = config or ContextBuilderConfig()

    def build(self, results: Iterable[SearchResult]) -> BuiltContext:
        selected: list[ContextChunk] = []
        seen_text_hashes: set[str] = set()
        total_tokens = 0
        skipped_duplicates = 0
        skipped_budget = 0

        for result in sorted(list(results), key=_stable_result_order):
            normalized_text = _normalize_text(result.text)
            if not normalized_text:
                continue

            text_hash = _text_hash(normalized_text)
            if text_hash in seen_text_hashes:
                skipped_duplicates += 1
                continue

            token_count = estimate_tokens(normalized_text)
            if token_count > self.config.max_tokens:
                normalized_text = truncate_to_token_budget(normalized_text, self.config.max_tokens)
                token_count = estimate_tokens(normalized_text)

            if total_tokens + token_count > self.config.max_tokens:
                skipped_budget += 1
                continue

            selected.append(
                ContextChunk(
                    document_id=result.document_id,
                    chunk_id=result.chunk_id,
                    text=normalized_text,
                    score=float(result.score),
                    token_count=token_count,
                    metadata=dict(result.metadata),
                )
            )
            seen_text_hashes.add(text_hash)
            total_tokens += token_count

            if len(selected) >= self.config.max_chunks:
                break

        return BuiltContext(
            text=self._render(selected),
            chunks=tuple(selected),
            total_tokens=total_tokens,
            skipped_duplicates=skipped_duplicates,
            skipped_budget=skipped_budget,
        )

    def _render(self, chunks: list[ContextChunk]) -> str:
        rendered: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            header = f"[Source {index}: document={chunk.document_id}, chunk={chunk.chunk_id}"
            if self.config.include_scores:
                header += f", score={chunk.score:.4f}"
            header += "]"
            rendered.append(f"{header}\n{chunk.text}")
        return self.config.separator.join(rendered)


def estimate_tokens(text: str) -> int:
    """Cheap deterministic token estimate for budget enforcement.

    Uses whitespace tokens as a conservative local approximation. This is not a
    model-specific tokenizer, but it is stable and sufficient for gate checks.
    """

    normalized = _normalize_text(text)
    return len(normalized.split()) if normalized else 0


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens < 1:
        raise ValueError("max_tokens must be >= 1")
    tokens = _normalize_text(text).split()
    return " ".join(tokens[:max_tokens])


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split())


def _text_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _stable_result_order(result: SearchResult) -> tuple[float, str, str]:
    return (-float(result.score), result.document_id, result.chunk_id)
