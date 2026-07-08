"""Offline, rule-based text classification of OCR'd content.

Deterministic and stdlib-only -> genuinely unit-testable green (no model). An
image/embedding classifier can later implement the same TextClassifier port.
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from secondbrain.vision.ports import Label

# class -> list of (weight, compiled pattern)
_RULES: dict[str, list[tuple[float, re.Pattern]]] = {
    "invoice": [(1.0, re.compile(p, re.I)) for p in
                (r"\binvoice\b", r"\brechnung\b", r"\bbetrag\b", r"amount due", r"\btotal\b",
                 r"\bIBAN\b", r"ust-id", r"\bvat\b", r"€\s?\d")],
    "email": [(1.0, re.compile(p, re.I)) for p in
              (r"^from:", r"^to:", r"^subject:", r"^betreff:", r"wrote:", r"gesendet:")],
    "code": [(1.0, re.compile(p)) for p in
             (r"\bdef\s+\w+\(", r"\bclass\s+\w+", r"\bimport\s+\w+", r"function\s+\w+\(",
              r"[{};]\s*$", r"</?\w+>")],
    "chat": [(1.0, re.compile(p)) for p in
             (r"\b\d{1,2}:\d{2}\b", r"^\w+:\s", r"typing\.\.\.")],
    "calendar": [(1.0, re.compile(p, re.I)) for p in
                 (r"\bmeeting\b", r"\btermin\b", r"\b\d{1,2}:\d{2}\s?(am|pm)\b", r"calendar", r"kalender")],
}


@runtime_checkable
class TextClassifier(Protocol):
    def classify_text(self, text: str) -> list[Label]: ...


class HeuristicTextClassifier:
    """Scores text against keyword/regex rules; returns labels sorted by score."""

    name = "heuristic-text"

    def __init__(self, *, min_score: float = 0.0) -> None:
        self.min_score = min_score

    def classify_text(self, text: str) -> list[Label]:
        if not text.strip():
            return [Label("empty", 1.0)]
        lines = text.splitlines()
        scores: dict[str, float] = {}
        for cls, rules in _RULES.items():
            hits = 0.0
            for weight, pattern in rules:
                if pattern.flags & re.MULTILINE or pattern.pattern.startswith("^"):
                    hits += weight * sum(1 for ln in lines if pattern.search(ln))
                else:
                    hits += weight * len(pattern.findall(text))
            if hits:
                scores[cls] = hits
        if not scores:
            return [Label("generic", 1.0)]
        total = sum(scores.values())
        labels = [Label(cls, round(score / total, 3)) for cls, score in scores.items()]
        labels.sort(key=lambda l: l.score, reverse=True)
        return [l for l in labels if l.score >= self.min_score] or [Label("generic", 1.0)]

    def top(self, text: str) -> Label:
        return self.classify_text(text)[0]
