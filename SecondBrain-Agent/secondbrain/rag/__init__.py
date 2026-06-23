"""RAG package exports with legacy function compatibility."""

from __future__ import annotations

import json
from pathlib import Path

from secondbrain.rag.hybrid_score import HybridScoreCalculator, HybridScoreWeights
from secondbrain.rag.vector_search_service import VectorSearchService
from secondbrain.utils import now_date
from secondbrain.vault_scan import iter_markdown, read_note, word_tokens


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    text = text.replace("\r\n", "\n")
    chunks: list[str] = []
    pos = 0
    while pos < len(text):
        chunk = text[pos : pos + size].strip()
        if chunk:
            chunks.append(chunk)
        pos += max(size - overlap, 1)
    return chunks


def build_rag_index(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    system = vault / settings.get("vault_folders", {}).get("system", "99_System") / "rag"
    system.mkdir(parents=True, exist_ok=True)
    target = system / "rag_index.json"

    index = []
    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        text = read_note(note)
        for i, chunk in enumerate(chunk_text(text)):
            index.append(
                {
                    "note": str(note.relative_to(vault)),
                    "stem": note.stem,
                    "chunk_id": i,
                    "tokens": sorted(list(word_tokens(chunk)))[:500],
                    "preview": chunk[:500],
                }
            )

    target.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    md = system / "RAG_Index.md"
    md.write_text(f"# RAG Index\n\nAktualisiert: {now_date()}\n\nChunks: {len(index)}\n", encoding="utf-8")
    return target


def search_rag(settings: dict, query: str, limit: int = 10) -> list[dict]:
    vault = Path(settings["vault_path"])
    index_path = vault / settings.get("vault_folders", {}).get("system", "99_System") / "rag" / "rag_index.json"
    if not index_path.exists():
        build_rag_index(settings)

    data = json.loads(index_path.read_text(encoding="utf-8"))
    q = word_tokens(query)
    scored = []
    for item in data:
        tokens = set(item.get("tokens", []))
        score = len(q & tokens)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, **item} for s, item in scored[:limit]]


def write_rag_answer(settings: dict, query: str) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("rag", "19_RAG")
    folder.mkdir(parents=True, exist_ok=True)
    results = search_rag(settings, query)

    safe = "".join(c if c.isalnum() else "-" for c in query.lower())[:80].strip("-") or "query"
    target = folder / f"{now_date()}_rag_{safe}.md"
    lines = [f"# RAG Suche: {query}", "", "## Treffer", ""]
    if not results:
        lines.append("- Keine Treffer.")
    for result in results:
        lines.append(f"- Score {result['score']} | [[{Path(result['stem']).stem}]] | `{result['note']}`")
        lines.append(f"  - Vorschau: {result['preview'][:200].replace(chr(10), ' ')}")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


__all__ = [
    "HybridScoreCalculator",
    "HybridScoreWeights",
    "VectorSearchService",
    "chunk_text",
    "build_rag_index",
    "search_rag",
    "write_rag_answer",
]
