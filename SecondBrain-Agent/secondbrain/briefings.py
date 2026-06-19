from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tasks

def write_daily_briefing(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("daily_briefings", "10_DailyBriefings")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_daily-briefing.md"

    open_tasks = []
    risks = []
    for note in iter_markdown(vault):
        text = read_note(note)
        for task in extract_tasks(text):
            if task.startswith("- [ ]"):
                open_tasks.append((task, note.stem))
        if "risiko" in text.lower() or "blockiert" in text.lower():
            risks.append(note.stem)

    lines = [
        f"# Daily Briefing {now_date()}",
        "",
        "## Fokus",
        "",
        "- Inbox prüfen",
        "- Review Queue prüfen",
        "- offene Aufgaben priorisieren",
        "",
        "## Offene Aufgaben",
        ""
    ]
    for task, source in open_tasks[:20]:
        lines.append(f"- {task} ([[{source}]])")
    if not open_tasks:
        lines.append("- Keine offenen Aufgaben erkannt.")

    lines += ["", "## Risiken / Blocker", ""]
    for r in sorted(set(risks))[:20]:
        lines.append(f"- [[{r}]]")
    if not risks:
        lines.append("- Keine Risiken erkannt.")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def write_evening_review(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / settings.get("vault_folders", {}).get("reviews", "11_Reviews")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_evening-review.md"

    lines = [
        f"# Evening Review {now_date()}",
        "",
        "## Heute erledigt",
        "",
        "- ",
        "",
        "## Neue Erkenntnisse",
        "",
        "- ",
        "",
        "## Offene Punkte",
        "",
        "- Review Queue prüfen",
        "- Daily Digest prüfen",
        "- Knowledge Gaps prüfen",
        "",
        "## Morgen",
        "",
        "- "
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
