from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note, note_type, extract_tags, extract_tasks

def write_data_warehouse_v2(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    base = vault / "71_DataWarehouse"
    base.mkdir(parents=True, exist_ok=True)
    created = []

    facts_documents = base / "facts_documents.md"
    facts_tasks = base / "facts_tasks.md"
    facts_decisions = base / "facts_decisions.md"
    facts_tags = base / "facts_tags.md"
    facts_projects = base / "facts_projects.md"

    type_counts = Counter()
    tag_counts = Counter()
    tasks = []
    decisions = []
    projects = []

    for note in iter_markdown(vault):
        text = read_note(note)
        low = text.lower()
        t = note_type(text) or "unknown"
        type_counts[t] += 1
        tag_counts.update(extract_tags(text))
        for task in extract_tasks(text):
            tasks.append((task, note.stem))
        for line in text.splitlines():
            if "entscheidung:" in line.lower():
                decisions.append((line.split(":",1)[-1].strip(), note.stem))
        if "01_Projekte" in note.parts or "type: project" in low:
            projects.append((note.stem, low.count("risiko"), len(extract_tasks(text))))

    facts_documents.write_text("# facts_documents\n\n| Typ | Anzahl |\n|---|---:|\n" + "\n".join(f"| {k} | {v} |" for k,v in type_counts.items()), encoding="utf-8")
    facts_tasks.write_text("# facts_tasks\n\n| Task | Quelle |\n|---|---|\n" + ("\n".join(f"| {t} | [[{s}]] |" for t,s in tasks) or "| keine | - |"), encoding="utf-8")
    facts_decisions.write_text("# facts_decisions\n\n| Entscheidung | Quelle |\n|---|---|\n" + ("\n".join(f"| {d} | [[{s}]] |" for d,s in decisions) or "| keine | - |"), encoding="utf-8")
    facts_tags.write_text("# facts_tags\n\n| Tag | Anzahl |\n|---|---:|\n" + "\n".join(f"| {k} | {v} |" for k,v in tag_counts.most_common()), encoding="utf-8")
    facts_projects.write_text("# facts_projects\n\n| Projekt | Risiken | Tasks |\n|---|---:|---:|\n" + ("\n".join(f"| [[{p}]] | {r} | {t} |" for p,r,t in projects) or "| keine | 0 | 0 |"), encoding="utf-8")

    return [facts_documents, facts_tasks, facts_decisions, facts_tags, facts_projects]
