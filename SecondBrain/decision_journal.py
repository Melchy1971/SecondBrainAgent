from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_decision_journal(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "53_DecisionJournal"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Decision_Journal.md"

    decisions = []
    for note in iter_markdown(vault):
        text = read_note(note)
        for line in text.splitlines():
            low = line.lower()
            if "entscheidung:" in low or "beschluss:" in low:
                decisions.append((line.split(":",1)[-1].strip(), note.stem))

    lines = ["# Decision Journal", "", f"Aktualisiert: {now_date()}", "", "| Entscheidung | Annahme | Alternative | Ergebnis | Quelle |", "|---|---|---|---|---|"]
    if not decisions:
        lines.append("| Keine Entscheidungen erkannt | - | - | - | - |")
    for d, src in decisions:
        lines.append(f"| {d} | offen | offen | offen | [[{src}]] |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
