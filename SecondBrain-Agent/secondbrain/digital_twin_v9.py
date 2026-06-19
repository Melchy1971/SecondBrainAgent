from pathlib import Path
from collections import Counter
from .v9_common import iter_md, read, tags, now_date, ensure

def write_digital_twin_v6(vault: Path) -> Path:
    folder = ensure(vault / "86_DigitalTwinV6")
    target = folder / "Digital_Twin_v6.md"
    tag_counter = Counter()
    signals = Counter()
    for p in iter_md(vault):
        text = read(p).lower()
        tag_counter.update(tags(read(p)))
        for s in ["stabilität", "automatisierung", "wartbarkeit", "lokal", "projekt", "prozess", "risiko", "entscheidung", "lernen", "gesundheit"]:
            signals[s] += text.count(s)
    lines = ["# Digital Twin v6", "", f"Aktualisiert: {now_date()}", "", "## Prioritätssignale", ""]
    for k, v in signals.most_common():
        if v:
            lines.append(f"- {k}: {v}")
    lines += ["", "## Wissensschwerpunkte", ""]
    for k, v in tag_counter.most_common(30):
        lines.append(f"- #{k}: {v}")
    lines += ["", "## Kernfragen", "", "- Welche Projekte passen zu meinen Zielen?", "- Welche Risiken ignoriere ich?", "- Welche Aufgaben sollte ich heute erledigen?"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
