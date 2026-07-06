"""v30.64 Agent Memory Injection - MemoryConflictDetector.

Surfaces memories that contradict each other so an agent is never silently fed
two incompatible facts. Two detectors:

* explicit  - records sharing a ``claim_key`` in metadata but asserting a
  different ``claim_value``.
* heuristic - records with high term overlap where exactly one carries a
  negation ("not", "kein", "no longer", ...).
"""

from __future__ import annotations

import re
from typing import Any

from .models import MemoryConflict

_WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+")

NEGATIONS = {"not", "no", "never", "none", "cannot", "cant",
             "kein", "keine", "nicht", "nie", "niemals", "ohne"}
_STOPWORDS = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "and", "or",
              "der", "die", "das", "ist", "sind", "und", "oder", "ein", "eine", "im", "in"}


def _content_terms(text: str) -> set[str]:
    return {t.lower() for t in _WORD.findall(text or "") if t.lower() not in _STOPWORDS}


def _has_negation(text: str) -> bool:
    tokens = {t.lower() for t in _WORD.findall(text or "")}
    if tokens & NEGATIONS:
        return True
    lowered = (text or "").lower()
    return "no longer" in lowered or "nicht mehr" in lowered


class MemoryConflictDetector:
    def __init__(self, *, overlap_threshold: float = 0.5):
        self.overlap_threshold = overlap_threshold

    def detect(self, records: list[Any]) -> list[MemoryConflict]:
        conflicts: list[MemoryConflict] = []
        seen: set[tuple[str, str]] = set()

        # 1) explicit claim_key / claim_value conflicts
        by_key: dict[str, list[Any]] = {}
        for rec in records:
            key = (getattr(rec, "metadata", {}) or {}).get("claim_key")
            if key:
                by_key.setdefault(str(key), []).append(rec)
        for key, group in by_key.items():
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    a, b = group[i], group[j]
                    va = (a.metadata or {}).get("claim_value")
                    vb = (b.metadata or {}).get("claim_value")
                    if va is not None and vb is not None and va != vb:
                        pair = tuple(sorted((a.memory_id, b.memory_id)))
                        if pair not in seen:
                            seen.add(pair)
                            conflicts.append(MemoryConflict(
                                memory_ids=pair, reason="claim_value_mismatch",
                                detail=f"{key}: {va!r} vs {vb!r}"))

        # 2) heuristic negation conflicts
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                a, b = records[i], records[j]
                pair = tuple(sorted((a.memory_id, b.memory_id)))
                if pair in seen:
                    continue
                ta, tb = _content_terms(a.text), _content_terms(b.text)
                if not ta or not tb:
                    continue
                jaccard = len(ta & tb) / len(ta | tb)
                if jaccard < self.overlap_threshold:
                    continue
                if _has_negation(a.text) != _has_negation(b.text):
                    seen.add(pair)
                    conflicts.append(MemoryConflict(
                        memory_ids=pair, reason="negation",
                        detail=f"overlap={jaccard:.2f}"))
        return conflicts
