from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_memory_replay(settings: dict, topic: str = "") -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "22_Memory"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_memory-replay.md"

    hits = []
    terms = [t.lower() for t in topic.split() if len(t) > 3]
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        if not terms or any(t in text for t in terms):
            if any(k in text for k in ["entscheidung", "meeting", "aufgabe", "risiko", "quelle"]):
                hits.append(note.stem)

    lines = ["# Agent Memory Replay", "", f"Thema: {topic or 'global'}", "", "## Verlaufskandidaten", ""]
    lines += [f"- [[{h}]]" for h in hits[:80]] or ["- Keine Kandidaten."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
