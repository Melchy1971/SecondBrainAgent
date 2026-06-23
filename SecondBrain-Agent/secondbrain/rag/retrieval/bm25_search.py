"""Lexical retrieval adapter with a dependency-free BM25 implementation."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Protocol

from .score_fusion import SearchResult

_TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)


class BM25Search(Protocol):
    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        ...


@dataclass(frozen=True)
class TextChunk:
    document_id: str
    chunk_id: str
    text: str


class InMemoryBM25Search:
    """BM25Okapi-style lexical search for local and test usage."""

    def __init__(self, chunks: Iterable[TextChunk], k1: float = 1.5, b: float = 0.75) -> None:
        self._chunks = list(chunks)
        self._k1 = k1
        self._b = b
        self._tokens = [_tokenize(chunk.text) for chunk in self._chunks]
        self._term_freqs = [Counter(tokens) for tokens in self._tokens]
        self._doc_lengths = [len(tokens) for tokens in self._tokens]
        self._avgdl = sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        self._doc_freq: Counter[str] = Counter()
        for tokens in self._tokens:
            self._doc_freq.update(set(tokens))

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        if limit <= 0:
            return []
        query_terms = _tokenize(query)
        if not query_terms:
            return []
        scored: list[SearchResult] = []
        for idx, chunk in enumerate(self._chunks):
            score = self._score(query_terms, idx)
            if score > 0:
                scored.append(
                    SearchResult(
                        document_id=chunk.document_id,
                        chunk_id=chunk.chunk_id,
                        text=chunk.text,
                        score=score,
                        metadata={"source": "bm25"},
                    )
                )
        return sorted(scored, key=lambda r: (-r.score, r.document_id, r.chunk_id))[:limit]

    def _score(self, terms: list[str], idx: int) -> float:
        total_docs = len(self._chunks)
        if total_docs == 0 or self._avgdl == 0:
            return 0.0
        score = 0.0
        freqs = self._term_freqs[idx]
        doc_len = self._doc_lengths[idx]
        for term in terms:
            tf = freqs.get(term, 0)
            if tf == 0:
                continue
            df = self._doc_freq.get(term, 0)
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            denominator = tf + self._k1 * (1 - self._b + self._b * doc_len / self._avgdl)
            score += idf * (tf * (self._k1 + 1)) / denominator
        return score


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text or "")]
