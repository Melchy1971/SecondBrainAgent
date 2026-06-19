from pathlib import Path
from .v97_common import VAULT, iter_notes, read, links, signals, now_date, ensure

def write_reasoning_map(vault: Path = VAULT) -> Path:
    target = ensure(vault / "102_ReasoningEngine") / f"{now_date()}_reasoning-map.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        impact = sig["risk"] * 3 + sig["decision"] * 2 + len(links(text))
        if impact:
            rows.append((impact, sig, p.stem))

    lines = ["# Reasoning Engine v9.7", "", f"Datum: {now_date()}", "", "| Impact | Notiz | Risiko | Entscheidung | Links | Interpretation |", "|---:|---|---:|---:|---:|---|"]
    for impact, sig, stem in sorted(rows, reverse=True)[:80]:
        interpretation = "Review priorisieren" if sig["risk"] else "Entscheidungskontext prüfen" if sig["decision"] else "Kontextknoten"
        lines.append(f"| {impact} | [[{stem}]] | {sig['risk']} | {sig['decision']} | {impact - sig['risk']*3 - sig['decision']*2} | {interpretation} |")
    if not rows:
        lines.append("| 0 | keine Signale | 0 | 0 | 0 | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
