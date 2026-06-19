from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def detect_healing_actions(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "99_System" / "self_healing"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_self-healing-report.md"

    missing_frontmatter = []
    broken_candidate_links = []
    all_stems = {p.stem for p in iter_markdown(vault)}

    for note in iter_markdown(vault):
        text = read_note(note)
        if not text.strip().startswith("---"):
            missing_frontmatter.append(note)
        # lightweight broken link scan
        import re
        for link in re.findall(r"\[\[([^\]]+)\]\]", text):
            clean = link.split("|")[0].split("#")[0]
            if clean and clean not in all_stems:
                broken_candidate_links.append((note, clean))

    lines = ["# Self-Healing Report", "", f"Datum: {now_date()}", "", "## Fehlendes Frontmatter", ""]
    lines += [f"- [[{p.stem}]]" for p in missing_frontmatter[:100]] or ["- Keine"]
    lines += ["", "## Potenziell kaputte Links", ""]
    lines += [f"- [[{p.stem}]] → [[{link}]]" for p, link in broken_candidate_links[:100]] or ["- Keine"]
    lines += ["", "## Sicherheitsregel", "", "- Automatische Reparatur wird nur vorbereitet, nicht destruktiv ausgeführt."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
