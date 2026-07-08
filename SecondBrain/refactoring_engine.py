from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags

def write_refactoring_proposals(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "41_Refactoring"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_refactoring-proposals.md"

    lines = ["# Autonomous Refactoring Proposals", "", f"Datum: {now_date()}", ""]
    count = 0
    for note in iter_markdown(vault):
        text = read_note(note)
        reasons = []
        if len(text) > 15000:
            reasons.append("Notiz sehr groß → aufteilen")
        if len(extract_tags(text)) > 8:
            reasons.append("zu viele Tags → reduzieren")
        if not text.strip().startswith("---"):
            reasons.append("Frontmatter ergänzen")
        if reasons:
            count += 1
            lines.append(f"## [[{note.stem}]]")
            for r in reasons:
                lines.append(f"- {r}")
            lines.append("")
    if count == 0:
        lines.append("- Keine Refactoring-Kandidaten.")
    lines += ["", "## Sicherheitsregel", "", "- Keine automatische Änderung ohne Bestätigung."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
