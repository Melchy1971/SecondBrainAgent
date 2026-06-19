from pathlib import Path
from collections import Counter, defaultdict
import re, json
from .v99_common import VAULT, iter_notes, read, tags, links, source_of, now_date, ensure, stem_id

ORG_HINTS = ["GmbH", "AG", "e.V.", "Telekom", "SAP", "OpenAI", "Google", "Microsoft", "Perplexity", "Anthropic"]
TECH_HINTS = ["Python", "Docker", "PostgreSQL", "Ollama", "Obsidian", "MCP", "React", "TypeScript", "SAP", "Claude", "Gemini", "ChatGPT"]
PROJECT_HINTS = ["Projekt", "Roadmap", "Sprint", "Release", "SecondBrain", "Jarvis", "Wissensdatenbank"]
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}|\d{2}\.\d{2}\.20\d{2})\b")
NAME_RE = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]+(?:\s[A-ZÄÖÜ][a-zäöüß]+){0,2}\b")

def classify_entity(value: str, context: str) -> str:
    if value in TECH_HINTS:
        return "technology"
    if any(h.lower() in value.lower() for h in ORG_HINTS):
        return "organization"
    if any(h.lower() in context.lower() for h in PROJECT_HINTS) and len(value) > 3:
        return "project_or_topic"
    if DATE_RE.match(value):
        return "date"
    return "person_or_topic"

def extract_entities_from_text(text: str) -> list[dict]:
    found = set()
    entities = []
    for d in DATE_RE.findall(text):
        found.add(("date", d))
    for t in TECH_HINTS:
        if re.search(rf"\b{re.escape(t)}\b", text, flags=re.IGNORECASE):
            found.add(("technology", t))
    for name in NAME_RE.findall(text[:12000]):
        if len(name) > 2 and name.lower() not in {"datum", "status", "quelle", "inhalt"}:
            found.add((classify_entity(name, text), name))
    for typ, val in sorted(found):
        entities.append({"type": typ, "value": val})
    return entities

def build_entity_index(vault: Path = VAULT) -> Path:
    system = ensure(vault / "99_System" / "entities")
    out_json = system / "entity_index.json"
    rows = []
    counts = Counter()
    by_source = defaultdict(Counter)

    for p in iter_notes(vault):
        text = read(p)
        src = source_of(text, p)
        ents = extract_entities_from_text(text)
        for e in ents:
            item = {"entity": e["value"], "type": e["type"], "note": p.stem, "path": str(p), "source": src}
            rows.append(item)
            counts[(e["type"], e["value"])] += 1
            by_source[src][e["type"]] += 1

    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ensure(vault / "113_EntityExtraction") / "Entity_Index.md"
    lines = ["# Entity Extraction v9.9", "", f"Aktualisiert: {now_date()}", "", "## Häufigste Entitäten", ""]
    for (typ, val), count in counts.most_common(100):
        lines.append(f"- **{val}** ({typ}): {count}")
    lines += ["", "## Quellenverteilung", ""]
    for src, counter in by_source.items():
        lines.append(f"### {src}")
        for typ, count in counter.most_common():
            lines.append(f"- {typ}: {count}")
    report.write_text("\n".join(lines), encoding="utf-8")
    return report
