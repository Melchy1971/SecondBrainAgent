from pathlib import Path
from collections import Counter
from .utils import now_date
from .vault_scan import iter_markdown, read_note

PROCESS_WORDS = ["freigabe", "genehmigung", "bestellung", "auftrag", "ticket", "incident", "review", "test", "prozess", "schnittstelle"]

def write_process_mining_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "30_ProcessMining"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_process-mining.md"

    counts = Counter()
    sources = {w: [] for w in PROCESS_WORDS}
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        for w in PROCESS_WORDS:
            c = text.count(w)
            if c:
                counts[w] += c
                sources[w].append(note.stem)

    lines = ["# Process Mining Report", "", f"Datum: {now_date()}", "", "| Signal | Gewicht | Quellen |", "|---|---:|---|"]
    for w, c in counts.most_common():
        lines.append(f"| {w} | {c} | {', '.join('[[%s]]' % s for s in sources[w][:5])} |")
    if not counts:
        lines.append("| keine | 0 | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
