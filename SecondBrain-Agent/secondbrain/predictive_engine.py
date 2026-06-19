from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note

def write_prediction_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "28_Predictions"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_prediction-report.md"

    signals = []
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        score = 0
        reasons = []
        for key in ["blockiert", "risiko", "offen", "fehlend", "warning", "fail", "blocked"]:
            if key in text:
                score += text.count(key)
                reasons.append(key)
        if score:
            signals.append((score, note.stem, sorted(set(reasons))))

    lines = ["# Prediction Report", "", f"Datum: {now_date()}", "", "| Risiko-Score | Notiz | Signale |", "|---:|---|---|"]
    if not signals:
        lines.append("| 0 | keine | - |")
    for score, note, reasons in sorted(signals, reverse=True)[:50]:
        lines.append(f"| {score} | [[{note}]] | {', '.join(reasons)} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
