from pathlib import Path
from collections import defaultdict
from .v10_common import VAULT, iter_notes, read, domain_of, open_tasks, signals, now_date, ensure

ERP_FOLDERS = {
    "Projekte": "Projects",
    "Beruf": "Projects",
    "Verein": "Verein",
    "Gesundheit": "Health",
    "Finanzen": "Finance",
    "Lernen": "Learning",
    "Reisen": "Travel",
    "Privat": "CRM",
}

def write_personal_erp(vault: Path = VAULT) -> list[Path]:
    base = ensure(vault / "124_PersonalERP")
    buckets = defaultdict(list)
    for p in iter_notes(vault):
        text = read(p)
        d = domain_of(p, text)
        buckets[d].append((p.stem, len(open_tasks(text)), signals(text)))
    outputs = []
    for domain, rows in buckets.items():
        folder = ensure(base / ERP_FOLDERS.get(domain, "Projects"))
        target = folder / f"{domain}_ERP_Index.md"
        lines = [f"# {domain} ERP Index", "", f"Aktualisiert: {now_date()}", "", "| Objekt | Aufgaben | Risiken | Entscheidungen |", "|---|---:|---:|---:|"]
        for stem, tasks, sig in sorted(rows)[:200]:
            lines.append(f"| [[{stem}]] | {tasks} | {sig['risk']} | {sig['decision']} |")
        target.write_text("\n".join(lines), encoding="utf-8")
        outputs.append(target)
    return outputs
