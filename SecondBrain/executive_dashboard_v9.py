from pathlib import Path
from .v9_common import iter_md, read, tasks, now_date, ensure

def write_executive_dashboard(vault: Path) -> Path:
    folder = ensure(vault / "81_ExecutiveDashboard")
    target = folder / "Executive_Dashboard_v9.md"

    files = list(iter_md(vault))
    open_tasks = 0
    risks = 0
    decisions = 0
    meetings = 0
    projects = 0

    for p in files:
        text = read(p).lower()
        open_tasks += sum(1 for t in tasks(text) if "- [ ]" in t)
        risks += text.count("risiko") + text.count("blockiert") + text.count("blocked")
        decisions += text.count("entscheidung") + text.count("beschluss")
        meetings += text.count("meeting") + text.count("protokoll")
        projects += 1 if "01_Projekte" in p.parts or "type: project" in text else 0

    lines = [
        "# Executive Dashboard v9",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "| KPI | Wert |",
        "|---|---:|",
        f"| Markdown-Dateien | {len(files)} |",
        f"| Projekte | {projects} |",
        f"| offene Aufgaben | {open_tasks} |",
        f"| Risiko-/Blocker-Signale | {risks} |",
        f"| Entscheidungs-Signale | {decisions} |",
        f"| Meeting-Signale | {meetings} |",
        "",
        "## Management-Fokus",
        "",
        "1. Höchste Risiken prüfen.",
        "2. Offene Aufgaben reduzieren.",
        "3. Entscheidungen mit fehlenden Alternativen ergänzen.",
        "4. Importquellen regelmäßig aktualisieren.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
