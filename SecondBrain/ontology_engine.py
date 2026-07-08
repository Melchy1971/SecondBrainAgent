from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note

NODE_HINTS = {
    "person": ["person", "kontakt", "ansprechpartner"],
    "project": ["projekt", "roadmap", "sprint"],
    "process": ["prozess", "workflow", "freigabe"],
    "decision": ["entscheidung", "beschluss"],
    "risk": ["risiko", "blocker", "blocked"],
    "task": ["aufgabe", "todo", "- [ ]"],
    "system": ["sap", "docker", "postgres", "obsidian", "ollama"],
}

def classify_node(text: str) -> str:
    low = text.lower()
    scores = {}
    for node, hints in NODE_HINTS.items():
        scores[node] = sum(low.count(h) for h in hints)
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "document"

def write_ontology_index(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "39_Ontology"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Ontology_Index.md"

    counts = Counter()
    examples = {}
    for note in iter_markdown(vault):
        text = read_note(note)
        node = classify_node(text)
        counts[node] += 1
        examples.setdefault(node, []).append(note.stem)

    lines = ["# Personal Ontology Index", "", f"Aktualisiert: {now_date()}", "", "| Node Type | Anzahl | Beispiele |", "|---|---:|---|"]
    for node, count in counts.most_common():
        lines.append(f"| {node} | {count} | {', '.join('[[%s]]' % e for e in examples[node][:5])} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
