from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

AGENT_PROFILES = {
    "Research": ["quelle", "wissenslücke", "recherche", "link"],
    "Project": ["projekt", "task", "risiko", "blockiert", "roadmap"],
    "Decision": ["entscheidung", "annahme", "alternative", "ergebnis"],
    "Meeting": ["meeting", "agenda", "protokoll", "teilnehmer"],
    "Calendar": ["termin", "deadline", "datum", "kalender"],
    "Process": ["prozess", "raci", "schnittstelle", "kpi"],
    "Executive": ["dashboard", "management", "status", "risiko"],
}

def write_agent_memory_v2(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    folder = vault / "73_DigitalTwin" / "AgentMemory"
    folder.mkdir(parents=True, exist_ok=True)
    notes = [(p.stem, read_note(p).lower(), extract_tags(read_note(p))) for p in iter_markdown(vault)]
    created = []
    for agent, hints in AGENT_PROFILES.items():
        hits = []
        tag_counter = Counter()
        for stem, text, tags in notes:
            score = sum(text.count(h) for h in hints)
            if score:
                hits.append((score, stem))
                tag_counter.update(tags)
        target = folder / f"{agent}_Agent_Memory_v2.md"
        lines = [f"# {agent} Agent Memory v2", "", f"Aktualisiert: {now_date()}", "", "## Relevante Notizen", ""]
        for score, stem in sorted(hits, reverse=True)[:50]:
            lines.append(f"- [[{stem}]] — Score {score}")
        if not hits:
            lines.append("- Keine Signale.")
        lines += ["", "## Gelernte Tags", ""]
        for tag, count in tag_counter.most_common(20):
            lines.append(f"- #{tag}: {count}")
        target.write_text("\n".join(lines), encoding="utf-8")
        created.append(target)
    return created
