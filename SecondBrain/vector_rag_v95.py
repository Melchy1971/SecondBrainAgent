from __future__ import annotations
from pathlib import Path
from collections import Counter
import json, math, re
from datetime import datetime

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INDEX = VAULT / "99_System" / "vector_rag" / "vector_index.json"
TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]{3,}")

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]

def chunks(text: str, size: int = 1800, overlap: int = 200) -> list[str]:
    if len(text) <= size:
        return [text]
    out = []
    pos = 0
    while pos < len(text):
        out.append(text[pos:pos+size])
        pos += max(1, size - overlap)
    return out

def vector(text: str) -> dict[str, float]:
    c = Counter(tokenize(text))
    total = sum(c.values()) or 1
    return {k: v / total for k, v in c.items()}

def cosine(a: dict, b: dict) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k]*b[k] for k in keys)
    na = math.sqrt(sum(x*x for x in a.values()))
    nb = math.sqrt(sum(x*x for x in b.values()))
    return dot/(na*nb) if na and nb else 0.0

def iter_notes(vault: Path = VAULT):
    return [p for p in vault.rglob("*.md") if ".obsidian" not in p.parts and "99_System" not in p.parts]

def build_vector_index(vault: Path = VAULT, index_path: Path = INDEX) -> Path:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    for note in iter_notes(vault):
        try:
            text = note.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, ch in enumerate(chunks(text)):
            entries.append({
                "note": note.stem,
                "path": str(note),
                "chunk": i,
                "text": ch[:2200],
                "vector": vector(ch),
            })
    index_path.write_text(json.dumps({
        "created": datetime.now().isoformat(timespec="seconds"),
        "count": len(entries),
        "entries": entries
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    report = vault / "88_VectorRAG" / "Vector_RAG_Index.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# Vector RAG Index\n\nChunks: {len(entries)}\n\nIndex: `{index_path}`\n", encoding="utf-8")
    return index_path

def search_vector(query: str, top_k: int = 8, vault: Path = VAULT, index_path: Path = INDEX) -> list[dict]:
    if not index_path.exists():
        build_vector_index(vault, index_path)
    data = json.loads(index_path.read_text(encoding="utf-8"))
    qv = vector(query)
    results = []
    for e in data.get("entries", []):
        score = cosine(qv, e.get("vector", {}))
        if score > 0:
            results.append({**e, "score": round(score, 4)})
    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

def write_rag_result(query: str, vault: Path = VAULT) -> Path:
    results = search_vector(query, vault=vault)
    target = vault / "88_VectorRAG" / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_rag_search.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# RAG Search: {query}", "", "| Score | Note | Chunk | Preview |", "|---:|---|---:|---|"]
    for r in results:
        preview = r["text"].replace("\n", " ")[:220]
        lines.append(f"| {r['score']} | [[{r['note']}]] | {r['chunk']} | {preview} |")
    if not results:
        lines.append("| 0 | keine Treffer | 0 | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
