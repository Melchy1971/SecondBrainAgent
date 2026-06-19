from pathlib import Path
import json
import re
from collections import Counter, defaultdict
from .utils import now_date
from .vault_scan import iter_markdown, read_note, note_type, extract_tags, extract_links

ENTITY_HINTS = {
    "person": ["person", "kontakt", "ansprechpartner", "teilnehmer"],
    "project": ["projekt", "roadmap", "sprint", "release"],
    "process": ["prozess", "workflow", "schnittstelle", "freigabe"],
    "decision": ["entscheidung", "beschluss", "festlegung"],
    "meeting": ["meeting", "termin", "agenda", "protokoll"],
    "task": ["aufgabe", "todo", "- [ ]"],
    "risk": ["risiko", "blocker", "blocked", "fail"],
    "system": ["sap", "docker", "postgres", "obsidian", "ollama", "mcp"],
    "document": ["pdf", "docx", "xlsx", "dokument", "quelle"],
}

def classify_entity(text: str) -> str:
    low = text.lower()
    scores = {k: sum(low.count(h) for h in hints) for k, hints in ENTITY_HINTS.items()}
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] else "document"

def edge_type_from_context(text: str, link: str) -> str:
    low = text.lower()
    if "block" in low or "blockiert" in low:
        return "blocks"
    if "entscheidung" in low:
        return "decides"
    if "risiko" in low:
        return "impacts"
    if "aufgabe" in low or "- [ ]" in low:
        return "creates_task"
    return "references"

def build_full_graph(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    system_dir = vault / "99_System" / "knowledge_graph"
    system_dir.mkdir(parents=True, exist_ok=True)
    target_json = system_dir / "full_knowledge_graph.json"

    nodes = []
    edges = []
    stems = set()

    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        text = read_note(note)
        entity = classify_entity(text)
        stems.add(note.stem)
        nodes.append({
            "id": note.stem,
            "path": str(note.relative_to(vault)),
            "entity_type": entity,
            "note_type": note_type(text) or "unknown",
            "tags": extract_tags(text),
        })
        for link in extract_links(text):
            target = link.split("|")[0].split("#")[0]
            if target:
                edges.append({
                    "source": note.stem,
                    "target": target,
                    "type": edge_type_from_context(text, target),
                    "weight": 1
                })

    graph = {"nodes": nodes, "edges": edges}
    target_json.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    out = vault / "66_KnowledgeGraph" / "Full_Knowledge_Graph.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(n["entity_type"] for n in nodes)
    edge_counts = Counter(e["type"] for e in edges)
    lines = ["# Full Knowledge Graph", "", f"Aktualisiert: {now_date()}", "", "## Nodes", ""]
    for k, v in counts.most_common():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Edges", ""]
    for k, v in edge_counts.most_common():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Graph JSON", "", f"`{target_json}`"]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
