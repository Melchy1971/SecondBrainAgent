from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

AGENTS = ["Research", "Project", "Process", "Executive", "ChiefOfStaff"]

def write_agent_memories(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    folder = vault / "48_AgentMemory"
    folder.mkdir(parents=True, exist_ok=True)
    created = []
    signals = {
        "Research": ["quelle", "research", "wissenslücke"],
        "Project": ["projekt", "task", "risiko", "blockiert"],
        "Process": ["prozess", "workflow", "schnittstelle", "kpi"],
        "Executive": ["entscheidung", "dashboard", "risiko", "kpi"],
        "ChiefOfStaff": ["priorität", "ziel", "blocker", "entscheidung"],
    }
    all_notes = [(p.stem, read_note(p).lower()) for p in iter_markdown(vault)]
    for agent in AGENTS:
        target = folder / f"{agent}_Memory.md"
        lines = [f"# {agent} Agent Memory", "", f"Aktualisiert: {now_date()}", "", "## Relevante Signale", ""]
        keys = signals[agent]
        hits = []
        for stem, text in all_notes:
            score = sum(text.count(k) for k in keys)
            if score:
                hits.append((score, stem))
        for score, stem in sorted(hits, reverse=True)[:50]:
            lines.append(f"- [[{stem}]] — Score {score}")
        if not hits:
            lines.append("- Keine Signale.")
        lines += ["", "## Lernhistorie", "", "- Wird über Agentenläufe erweitert."]
        target.write_text("\n".join(lines), encoding="utf-8")
        created.append(target)
    return created
