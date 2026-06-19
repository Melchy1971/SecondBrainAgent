from pathlib import Path
from .v98_common import VAULT, iter_notes, read, signals, now_date, ensure

def write_process_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "111_ProcessAgent") / f"{now_date()}_process-agent.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        low = text.lower()
        if sig["process"] or "prozess" in low or "workflow" in low:
            bottleneck = low.count("warte") + low.count("manuell") + low.count("fehler") + low.count("blockiert")
            rows.append((sig["process"] + bottleneck*3 + sig["risk"]*2, p.stem, bottleneck, sig))
    lines = ["# Process Agent v9.8", "", f"Datum: {now_date()}", "", "| Score | Prozess | Bottleneck | Risiken | Empfehlung |", "|---:|---|---:|---:|---|"]
    for score, stem, bottleneck, sig in sorted(rows, reverse=True)[:80]:
        rec = "Automatisierung prüfen" if bottleneck else "Prozessmodell ergänzen"
        lines.append(f"| {score} | [[{stem}]] | {bottleneck} | {sig['risk']} | {rec} |")
    if not rows:
        lines.append("| 0 | keine Prozesse erkannt | 0 | 0 | Prozessnotizen importieren |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
