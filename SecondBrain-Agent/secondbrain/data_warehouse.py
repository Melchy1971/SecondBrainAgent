from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, note_type, extract_tasks

def write_data_warehouse(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    base = vault / "59_DataWarehouse"
    facts = base / "Facts"
    dims = base / "Dimensions"
    facts.mkdir(parents=True, exist_ok=True)
    dims.mkdir(parents=True, exist_ok=True)

    fact_docs = facts / "facts_documents.md"
    fact_tasks = facts / "facts_tasks.md"
    fact_decisions = facts / "facts_decisions.md"
    dim_types = dims / "dim_note_types.md"

    type_counts = {}
    task_rows = []
    decision_rows = []

    for note in iter_markdown(vault):
        text = read_note(note)
        t = note_type(text) or "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1
        for task in extract_tasks(text):
            task_rows.append((task, note.stem))
        for line in text.splitlines():
            if "entscheidung:" in line.lower():
                decision_rows.append((line.split(":",1)[-1].strip(), note.stem))

    fact_docs.write_text("# facts_documents\n\n| Notiztyp | Anzahl |\n|---|---:|\n" + "\n".join(f"| {k} | {v} |" for k,v in sorted(type_counts.items())), encoding="utf-8")
    fact_tasks.write_text("# facts_tasks\n\n| Task | Quelle |\n|---|---|\n" + ("\n".join(f"| {t} | [[{s}]] |" for t,s in task_rows) or "| keine | - |"), encoding="utf-8")
    fact_decisions.write_text("# facts_decisions\n\n| Entscheidung | Quelle |\n|---|---|\n" + ("\n".join(f"| {d} | [[{s}]] |" for d,s in decision_rows) or "| keine | - |"), encoding="utf-8")
    dim_types.write_text("# dim_note_types\n\nAktualisiert: " + now_date() + "\n", encoding="utf-8")
    return [fact_docs, fact_tasks, fact_decisions, dim_types]
