from pathlib import Path
import json
import math
import re
from collections import Counter
from .utils import now_date, slugify
from .vault_scan import iter_markdown, read_note, note_type, extract_tags, extract_links

TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9]{3,}")

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]

def vectorize(text: str) -> dict:
    counts = Counter(tokenize(text))
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}

def cosine(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v*v for v in a.values()))
    nb = math.sqrt(sum(v*v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

def build_semantic_index(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "semantic_search"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "semantic_index.json"

    entries = []
    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        text = read_note(note)
        entries.append({
            "path": str(note.relative_to(vault)),
            "stem": note.stem,
            "type": note_type(text) or "unknown",
            "tags": extract_tags(text),
            "links": extract_links(text),
            "vector": vectorize(text[:20000]),
            "preview": text[:500],
        })

    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    md = vault / "65_SemanticSearch" / "Semantic_Index.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(f"# Semantic Index\n\nAktualisiert: {now_date()}\n\nNotizen: {len(entries)}\n", encoding="utf-8")
    return target

def semantic_search(settings: dict, query: str, limit: int = 20) -> list[dict]:
    vault = Path(settings["vault_path"])
    index_path = vault / "99_System" / "semantic_search" / "semantic_index.json"
    if not index_path.exists():
        build_semantic_index(settings)
    data = json.loads(index_path.read_text(encoding="utf-8"))
    qv = vectorize(query)
    results = []
    q_tokens = set(tokenize(query))
    for e in data:
        score_sem = cosine(qv, e.get("vector", {}))
        score_kw = len(q_tokens & set(tokenize(e.get("preview", "")))) / (len(q_tokens) or 1)
        score = (score_sem * 0.7) + (score_kw * 0.3)
        if score > 0:
            results.append({**e, "score": round(score, 4)})
    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

def write_search_result(settings: dict, query: str) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "65_SemanticSearch"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_search_{slugify(query)}.md"
    results = semantic_search(settings, query)
    lines = [f"# Semantic Search: {query}", "", f"Datum: {now_date()}", "", "| Score | Notiz | Typ | Tags |", "|---:|---|---|---|"]
    if not results:
        lines.append("| 0 | keine Treffer | - | - |")
    for r in results:
        tags = ", ".join(r.get("tags", []))
        lines.append(f"| {r['score']} | [[{r['stem']}]] | {r.get('type')} | {tags} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
