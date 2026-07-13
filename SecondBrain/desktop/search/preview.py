from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class SearchPreviewSettings:
    max_snippet_chars: int = 280
    context_chars: int = 70
    max_highlights: int = 8
    marker_start: str = "<mark>"
    marker_end: str = "</mark>"
    escape_html: bool = True

    def normalized(self) -> "SearchPreviewSettings":
        return SearchPreviewSettings(
            max_snippet_chars=max(40, min(int(self.max_snippet_chars), 2000)),
            context_chars=max(10, min(int(self.context_chars), 300)),
            max_highlights=max(0, min(int(self.max_highlights), 50)),
            marker_start=str(self.marker_start),
            marker_end=str(self.marker_end),
            escape_html=bool(self.escape_html),
        )


@dataclass(frozen=True)
class SearchHighlight:
    term: str
    start: int
    end: int

    def as_dict(self) -> dict[str, Any]:
        return {"term": self.term, "start": self.start, "end": self.end}


@dataclass(frozen=True)
class SearchPreview:
    document_id: str
    title: str
    snippet: str
    highlighted_snippet: str
    highlights: list[SearchHighlight] = field(default_factory=list)
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "snippet": self.snippet,
            "highlighted_snippet": self.highlighted_snippet,
            "highlights": [h.as_dict() for h in self.highlights],
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }


class SearchPreviewBuilder:
    """Builds safe, bounded previews for desktop search results."""

    def __init__(self, settings: SearchPreviewSettings | None = None) -> None:
        self.settings = (settings or SearchPreviewSettings()).normalized()

    def build(self, result: Any, query_text: str | None = None, *, content: str | None = None) -> SearchPreview:
        source_text = self._source_text(result, content)
        terms = self._extract_terms(query_text or "")
        snippet, offset, truncated = self._make_snippet(source_text, terms)
        local_highlights = self._find_highlights(snippet, terms)
        highlighted = self._apply_highlights(snippet, local_highlights)
        return SearchPreview(
            document_id=str(getattr(result, "document_id", "")),
            title=str(getattr(result, "title", "Untitled")),
            snippet=snippet,
            highlighted_snippet=highlighted,
            highlights=[SearchHighlight(h.term, h.start + offset, h.end + offset) for h in local_highlights],
            truncated=truncated,
            metadata={
                "preview_source": "content" if content is not None else "result_snippet",
                "query_terms": terms,
                "snippet_offset": offset,
            },
        )

    def build_many(self, results: Iterable[Any], query_text: str | None = None) -> list[SearchPreview]:
        return [self.build(result, query_text) for result in results]

    def _source_text(self, result: Any, content: str | None) -> str:
        raw = content if content is not None else getattr(result, "snippet", "")
        return re.sub(r"\s+", " ", str(raw or "")).strip()

    def _extract_terms(self, query_text: str) -> list[str]:
        raw_terms = re.findall(r"[\wÄÖÜäöüß-]{2,}", query_text.lower())
        seen: set[str] = set()
        terms: list[str] = []
        for term in raw_terms:
            if term not in seen:
                seen.add(term)
                terms.append(term)
        return terms[: self.settings.max_highlights]

    def _make_snippet(self, text: str, terms: list[str]) -> tuple[str, int, bool]:
        if not text:
            return "", 0, False
        max_chars = self.settings.max_snippet_chars
        first_match = self._first_match_index(text, terms)
        if len(text) <= max_chars:
            return text, 0, False
        if first_match < 0:
            return text[:max_chars].rstrip() + "…", 0, True
        start = max(0, first_match - self.settings.context_chars)
        end = min(len(text), start + max_chars)
        start = max(0, end - max_chars)
        snippet = text[start:end].strip()
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        return f"{prefix}{snippet}{suffix}", start, True

    def _first_match_index(self, text: str, terms: list[str]) -> int:
        lower = text.lower()
        indices = [lower.find(term) for term in terms if lower.find(term) >= 0]
        return min(indices) if indices else -1

    def _find_highlights(self, snippet: str, terms: list[str]) -> list[SearchHighlight]:
        highlights: list[SearchHighlight] = []
        occupied: list[range] = []
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(snippet):
                candidate = range(match.start(), match.end())
                if any(set(candidate).intersection(existing) for existing in occupied):
                    continue
                highlights.append(SearchHighlight(term=match.group(0), start=match.start(), end=match.end()))
                occupied.append(candidate)
                if len(highlights) >= self.settings.max_highlights:
                    return sorted(highlights, key=lambda h: (h.start, h.end))
        return sorted(highlights, key=lambda h: (h.start, h.end))

    def _apply_highlights(self, snippet: str, highlights: list[SearchHighlight]) -> str:
        escaper = html.escape if self.settings.escape_html else (lambda value: value)
        if not highlights:
            return escaper(snippet)
        parts: list[str] = []
        cursor = 0
        for highlight in highlights:
            parts.append(escaper(snippet[cursor:highlight.start]))
            parts.append(self.settings.marker_start)
            parts.append(escaper(snippet[highlight.start:highlight.end]))
            parts.append(self.settings.marker_end)
            cursor = highlight.end
        parts.append(escaper(snippet[cursor:]))
        return "".join(parts)
