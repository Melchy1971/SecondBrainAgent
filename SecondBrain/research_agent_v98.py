from pathlib import Path
from .v98_common import VAULT, iter_notes, read, signals, now_date, ensure

def write_research_agent(vault: Path = VAULT) -> Path:
    target = ensure(vault / "107_ResearchAgent") / f"{now_date()}_research-backlog-agent.md"
    candidates = []
    for p in iter_notes(vault):
        text = read(p)
        low = text.lower()
        score = low.count("wissenslücke") + low.count("todo recherche") + low.count("unklar") + low.count("prüfen") + signals(text)["research"]
        if score:
            candidates.append((score, p.stem))
    lines = ["# Research Agent v9.8", "", f"Datum: {now_date()}", "", "| Score | Thema | Auftrag |", "|---:|---|---|"]
    for score, stem in sorted(candidates, reverse=True)[:60]:
        lines.append(f"| {score} | [[{stem}]] | Recherchefrage konkretisieren, Quellenbedarf festlegen |")
    if not candidates:
        lines.append("| 0 | keine expliziten Recherche-Signale | - |")
    lines += ["", "## Sicherheitsregel", "", "- Keine automatische Webrecherche ohne explizite Freigabe."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
