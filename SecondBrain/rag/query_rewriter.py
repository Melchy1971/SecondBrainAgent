"""P1 v19.5 - deterministic query rewriting.

Purpose:
- Normalize user queries.
- Generate conservative keyword variants.
- Avoid hallucinated expansion.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryRewriteResult:
    original: str
    normalized: str
    variants: list[str]


class QueryRewriter:
    def rewrite(self, query: str) -> QueryRewriteResult:
        original = query or ""
        normalized = " ".join(original.strip().split())
        variants = [normalized] if normalized else []

        lower = normalized.lower()
        replacements = {
            "e-mail": "email",
            "emails": "email",
            "dokumente": "dokument",
            "dateien": "datei",
            "termine": "termin",
        }

        for source, target in replacements.items():
            if source in lower:
                candidate = lower.replace(source, target)
                if candidate and candidate not in variants:
                    variants.append(candidate)

        tokens = [t for t in lower.split() if len(t) > 2]
        if len(tokens) >= 2:
            compact = " ".join(tokens)
            if compact not in variants:
                variants.append(compact)

        return QueryRewriteResult(original=original, normalized=normalized, variants=variants[:5])
