from pathlib import Path
from .utils import now_date

def write_decision_intelligence(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "12_Decisions"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_decision-intelligence.md"

    lines = [
        "# Decision Intelligence",
        "",
        f"Datum: {now_date()}",
        "",
        "## Prüffragen",
        "",
        "- Welche Entscheidungen haben keine dokumentierte Alternative?",
        "- Welche Entscheidungen haben kein Risiko?",
        "- Welche Entscheidungen haben kein Ergebnis?",
        "- Welche Entscheidungen betreffen mehrere Projekte?",
        "",
        "## Nächste Aktion",
        "",
        "- Decision Register prüfen und fehlende Felder ergänzen."
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
