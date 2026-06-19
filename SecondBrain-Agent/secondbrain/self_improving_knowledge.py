from pathlib import Path
from .utils import now_date
from .quality_scoring import score_note
from .vault_scan import iter_markdown, read_note

def write_self_improvement_plan(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "74_SelfImprovingKnowledge"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_self-improvement-plan.md"

    candidates = []
    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        score = score_note(read_note(note))
        if score < 60:
            candidates.append((score, note.stem))

    lines = ["# Self-Improving Knowledge Plan", "", f"Datum: {now_date()}", "", "| Score | Notiz | Maßnahme |", "|---:|---|---|"]
    if not candidates:
        lines.append("| 100 | keine Kandidaten | keine |")
    for score, stem in sorted(candidates)[:100]:
        lines.append(f"| {score} | [[{stem}]] | Titel/Tags/Links/Zusammenfassung ergänzen |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
