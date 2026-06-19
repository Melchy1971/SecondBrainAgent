
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math
import re
import time

TOKEN_RE = re.compile(r"[\wÄÖÜäöüß]{2,}", re.UNICODE)
STOPWORDS = {
    "der","die","das","und","oder","aber","mit","von","für","auf","aus","ist","sind","ein","eine","einer","einen","dem","den","des","im","in","zu","am","an","als","bei","wie","was","wer","wenn","dass","nicht","auch","this","that","with","from","into","the","and","or","for","are","is","to","of","a","an"
}

@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    path: str
    title: str
    text: str
    source_type: str = "markdown"
    mtime: float = 0.0

@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source_id: str
    path: str
    title: str
    ordinal: int
    text: str
    tokens: list[str]
    fingerprint: str
    mtime: float
    quality_score: float
    trust_score: float
    freshness_score: float

@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    source_id: str
    path: str
    title: str
    score: float
    lexical_score: float
    semantic_score: float
    quality_score: float
    trust_score: float
    freshness_score: float
    citation: str
    preview: str

@dataclass(frozen=True)
class RagAnswer:
    query: str
    answer: str
    hits: list[SearchHit]
    citations: list[str]


def tokenize(text: str) -> list[str]:
    tokens = [m.group(0).lower() for m in TOKEN_RE.finditer(text)]
    return [t for t in tokens if t not in STOPWORDS and not t.isdigit()]


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def source_id_for_path(path: Path, base: Path) -> str:
    try:
        rel = path.relative_to(base)
    except ValueError:
        rel = path
    return fingerprint(str(rel).replace("\\", "/"))


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = "Intro"
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                sections.append((current_title, "\n".join(current).strip()))
                current = []
            current_title = line.lstrip("#").strip() or current_title
        else:
            current.append(line)
    if current:
        sections.append((current_title, "\n".join(current).strip()))
    return [(t, body) for t, body in sections if body]


def chunk_text(text: str, max_chars: int = 1400, overlap: int = 180) -> list[str]:
    chunks: list[str] = []
    for _, section in split_markdown_sections(text) or [("", text)]:
        body = section.strip()
        if len(body) <= max_chars:
            if body:
                chunks.append(body)
            continue
        start = 0
        step = max(max_chars - overlap, 1)
        while start < len(body):
            candidate = body[start:start + max_chars]
            cut = max(candidate.rfind("\n\n"), candidate.rfind(". "), candidate.rfind("\n"))
            if cut > int(max_chars * 0.55):
                candidate = candidate[:cut + 1]
            candidate = candidate.strip()
            if candidate:
                chunks.append(candidate)
            start += step
    return chunks


def quality_score(text: str) -> float:
    length = len(text)
    token_count = len(tokenize(text))
    has_heading = 1.0 if "#" in text[:80] else 0.0
    has_structure = 1.0 if any(marker in text for marker in ["- ", "1.", "##", ":"]) else 0.0
    length_score = min(length / 900.0, 1.0)
    density_score = min(token_count / 120.0, 1.0)
    return round(0.45 * length_score + 0.35 * density_score + 0.10 * has_heading + 0.10 * has_structure, 4)


def freshness_score(mtime: float, now: float | None = None) -> float:
    if not mtime:
        return 0.5
    now = now or time.time()
    age_days = max((now - mtime) / 86400, 0)
    return round(1.0 / (1.0 + age_days / 180.0), 4)


def trust_score(path: str) -> float:
    lowered = path.lower().replace("\\", "/")
    if any(part in lowered for part in ["/docs/", "docs/", "masterplan", "architecture", "security"]):
        return 0.95
    if any(part in lowered for part in ["inbox", "quick", "capture"]):
        return 0.65
    if any(part in lowered for part in ["archive", "old", "tmp"]):
        return 0.55
    return 0.8


def iter_source_documents(vault: Path, include_extensions: set[str] | None = None) -> Iterable[SourceDocument]:
    include_extensions = include_extensions or {".md", ".txt"}
    ignore_parts = {".git", ".venv", "node_modules", "__pycache__"}
    for path in sorted(vault.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in include_extensions:
            continue
        if any(part in ignore_parts for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.strip():
            continue
        title = path.stem
        first_heading = next((l.lstrip("#").strip() for l in text.splitlines() if l.startswith("#")), "")
        if first_heading:
            title = first_heading
        yield SourceDocument(
            source_id=source_id_for_path(path, vault),
            path=str(path.relative_to(vault)),
            title=title,
            text=text,
            source_type=path.suffix.lower().lstrip("."),
            mtime=path.stat().st_mtime,
        )


class AdvancedRagIndex:
    def __init__(self, vault: str | Path, index_path: str | Path | None = None):
        self.vault = Path(vault).resolve()
        self.index_path = Path(index_path).resolve() if index_path else self.vault / "99_System" / "rag_v109" / "advanced_rag_index.json"
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def build(self) -> dict[str, Any]:
        chunks: list[KnowledgeChunk] = []
        documents = list(iter_source_documents(self.vault))
        for doc in documents:
            for ordinal, chunk in enumerate(chunk_text(doc.text)):
                fp = fingerprint(chunk)
                chunk_id = f"{doc.source_id}:{ordinal}:{fp[:8]}"
                chunks.append(KnowledgeChunk(
                    chunk_id=chunk_id,
                    source_id=doc.source_id,
                    path=doc.path,
                    title=doc.title,
                    ordinal=ordinal,
                    text=chunk,
                    tokens=sorted(set(tokenize(chunk))),
                    fingerprint=fp,
                    mtime=doc.mtime,
                    quality_score=quality_score(chunk),
                    trust_score=trust_score(doc.path),
                    freshness_score=freshness_score(doc.mtime),
                ))
        payload = {
            "version": "10.9",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "vault": str(self.vault),
            "documents": len(documents),
            "chunks": [asdict(c) for c in chunks],
        }
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"documents": len(documents), "chunks": len(chunks), "index_path": str(self.index_path)}

    def load(self) -> dict[str, Any]:
        if not self.index_path.exists():
            self.build()
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def search(self, query: str, limit: int = 8) -> list[SearchHit]:
        data = self.load()
        q_tokens = set(tokenize(query))
        if not q_tokens:
            return []
        scored: list[SearchHit] = []
        for item in data.get("chunks", []):
            tokens = set(item.get("tokens", []))
            overlap = q_tokens & tokens
            if not overlap:
                continue
            lexical = len(overlap) / max(len(q_tokens), 1)
            semantic = len(overlap) / math.sqrt(max(len(tokens), 1))
            quality = float(item.get("quality_score", 0.5))
            trust = float(item.get("trust_score", 0.8))
            fresh = float(item.get("freshness_score", 0.5))
            score = (0.46 * lexical) + (0.24 * semantic) + (0.14 * quality) + (0.10 * trust) + (0.06 * fresh)
            preview = re.sub(r"\s+", " ", item.get("text", "")).strip()[:360]
            citation = f"{item.get('path')}#chunk-{item.get('ordinal')}"
            scored.append(SearchHit(
                chunk_id=item["chunk_id"],
                source_id=item["source_id"],
                path=item["path"],
                title=item.get("title", Path(item["path"]).stem),
                score=round(score, 5),
                lexical_score=round(lexical, 5),
                semantic_score=round(semantic, 5),
                quality_score=quality,
                trust_score=trust,
                freshness_score=fresh,
                citation=citation,
                preview=preview,
            ))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:limit]

    def answer(self, query: str, limit: int = 5) -> RagAnswer:
        hits = self.search(query, limit=limit)
        if not hits:
            answer = "Keine belastbaren Treffer im lokalen Wissensbestand gefunden."
            return RagAnswer(query=query, answer=answer, hits=[], citations=[])
        lines = [f"Antwort auf Basis von {len(hits)} lokalen Quellen:", ""]
        for i, hit in enumerate(hits, 1):
            lines.append(f"{i}. {hit.title}: {hit.preview}")
        citations = [h.citation for h in hits]
        lines.append("")
        lines.append("Quellen: " + "; ".join(citations))
        return RagAnswer(query=query, answer="\n".join(lines), hits=hits, citations=citations)

    def write_answer(self, query: str, output_dir: str | Path | None = None, limit: int = 5) -> Path:
        result = self.answer(query, limit=limit)
        output = Path(output_dir) if output_dir else self.vault / "19_RAG" / "answers"
        output.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^a-zA-Z0-9ÄÖÜäöüß_-]+", "-", query).strip("-")[:80] or "query"
        target = output / f"rag_v109_{time.strftime('%Y%m%d_%H%M%S')}_{safe}.md"
        lines = [f"# RAG v10.9 Antwort", "", f"Query: `{query}`", "", result.answer, "", "## Treffer", ""]
        for hit in result.hits:
            lines.append(f"- Score `{hit.score}` | `{hit.citation}` | {hit.title}")
        target.write_text("\n".join(lines), encoding="utf-8")
        return target


def build_advanced_rag(vault: str | Path, index_path: str | Path | None = None) -> dict[str, Any]:
    return AdvancedRagIndex(vault, index_path).build()


def search_advanced_rag(vault: str | Path, query: str, limit: int = 8, index_path: str | Path | None = None) -> list[dict[str, Any]]:
    return [asdict(h) for h in AdvancedRagIndex(vault, index_path).search(query, limit)]


def answer_advanced_rag(vault: str | Path, query: str, limit: int = 5, index_path: str | Path | None = None) -> dict[str, Any]:
    answer = AdvancedRagIndex(vault, index_path).answer(query, limit)
    return {"query": answer.query, "answer": answer.answer, "citations": answer.citations, "hits": [asdict(h) for h in answer.hits]}
