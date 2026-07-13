from pathlib import Path
from .v97_common import VAULT, iter_notes, read, signals, open_tasks, now_date, ensure

def write_self_reflection(vault: Path = VAULT) -> Path:
    target = ensure(vault / "101_SelfReflection") / f"{now_date()}_self-reflection.md"
    risks = []
    decisions = []
    weak = []
    tasks = []

    for p in iter_notes(vault):
        text = read(p)
        sig = signals(text)
        if sig["risk"]:
            risks.append((sig["risk"], p.stem))
        if sig["decision"]:
            decisions.append((sig["decision"], p.stem))
        if len(text.strip()) < 250 or not text.strip().startswith("---"):
            weak.append(p.stem)
        ot = open_tasks(text)
        if ot:
            tasks.append((len(ot), p.stem))

    lines = ["# Self Reflection v9.7", "", f"Datum: {now_date()}", "", "## Was wurde gelernt?", ""]
    lines.append(f"- Neue/aktive Wissensobjekte: {len(list(iter_notes(vault)))}")
    lines += ["", "## Was fehlt?", ""]
    lines.append(f"- Schwache Notizen: {len(weak)}")
    lines.append(f"- Offene Aufgabenbereiche: {len(tasks)}")
    lines += ["", "## Welche Risiken bestehen?", ""]
    for score, stem in sorted(risks, reverse=True)[:20]:
        lines.append(f"- [[{stem}]] — Risiko-Signale: {score}")
    if not risks:
        lines.append("- Keine starken Risiko-Signale.")
    lines += ["", "## Welche Entscheidungen brauchen Review?", ""]
    for score, stem in sorted(decisions, reverse=True)[:20]:
        lines.append(f"- [[{stem}]] — Entscheidungs-Signale: {score}")
    if not decisions:
        lines.append("- Keine.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
