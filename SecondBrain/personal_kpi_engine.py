from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tasks

def write_kpi_dashboard(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "52_KPIs"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_personal-kpis.md"

    notes = list(iter_markdown(vault))
    open_tasks = 0
    done_tasks = 0
    risks = 0
    for note in notes:
        text = read_note(note).lower()
        for t in extract_tasks(text):
            if t.startswith("- [ ]"):
                open_tasks += 1
            elif t.lower().startswith("- [x]"):
                done_tasks += 1
        risks += text.count("risiko") + text.count("blockiert") + text.count("blocked")

    lines = [
        "# Personal KPI Dashboard",
        "",
        f"Datum: {now_date()}",
        "",
        "| Bereich | KPI | Wert |",
        "|---|---|---:|",
        f"| Wissen | Markdown-Dateien | {len(notes)} |",
        f"| Aufgaben | offen | {open_tasks} |",
        f"| Aufgaben | erledigt | {done_tasks} |",
        f"| Projekte | Risiko-/Blocker-Signale | {risks} |",
        "| Gesundheit | Gewicht/HbA1c/Schritte | manuell anbinden |",
        "| Finanzen | Ausgaben/Sparquote | vorbereitet |",
        "| Lernen | Lernstunden/Themen | vorbereitet |",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
