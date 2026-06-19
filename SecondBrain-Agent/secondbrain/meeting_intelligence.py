from pathlib import Path
from .utils import now_date, slugify, ensure_unique_path
from .vault_scan import read_note

def analyze_meeting_file(settings: dict, source: Path) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("meetings", "13_Meetings")
    folder.mkdir(parents=True, exist_ok=True)

    text = read_note(source)
    title = source.stem
    target = ensure_unique_path(folder / f"{now_date()}_{slugify(title)}_meeting-analysis.md")

    tasks = []
    decisions = []
    for line in text.splitlines():
        low = line.lower()
        if "aufgabe:" in low or "todo:" in low:
            tasks.append(line.split(":", 1)[-1].strip())
        if "entscheidung:" in low or "beschluss:" in low:
            decisions.append(line.split(":", 1)[-1].strip())

    md = [
        f"# Meeting Analyse: {title}",
        "",
        f"Quelle: `{source}`",
        "",
        "## Zusammenfassung",
        "",
        text[:1000],
        "",
        "## Entscheidungen",
        ""
    ]
    md += [f"- {d}" for d in decisions] or ["- Keine erkannt."]
    md += ["", "## Aufgaben", ""]
    md += [f"- [ ] {t}" for t in tasks] or ["- Keine erkannt."]
    target.write_text("\n".join(md), encoding="utf-8")
    return target
