from pathlib import Path
from .utils import now_date

def write_chief_of_staff_v2(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "35_ChiefOfStaff"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_chief-of-staff-v2.md"

    lines = [
        f"# AI Chief of Staff {now_date()}",
        "",
        "## Lagebild",
        "",
        "- Daily Briefing prüfen.",
        "- Executive Dashboard prüfen.",
        "- Prediction Report prüfen.",
        "- Process Mining Report prüfen.",
        "",
        "## Entscheidungsvorbereitung",
        "",
        "- Fehlende Entscheidungen aus Decision Intelligence ergänzen.",
        "- Risiken mit höchstem Prediction Score priorisieren.",
        "",
        "## Arbeitsauftrag",
        "",
        "- Inbox leeren.",
        "- Review Queue bearbeiten.",
        "- Wissenslücken mit hoher Relevanz schließen."
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
