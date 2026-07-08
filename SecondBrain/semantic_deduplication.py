from pathlib import Path
from collections import defaultdict
from .utils import now_date
from .vault_scan import iter_markdown, read_note, word_tokens

def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def write_semantic_dedup_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "26_Deduplication"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_semantic-deduplication.md"

    notes = []
    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        tokens = word_tokens(read_note(note))
        if tokens:
            notes.append((note, tokens))

    pairs = []
    for i in range(len(notes)):
        for j in range(i+1, min(i+80, len(notes))):
            score = jaccard(notes[i][1], notes[j][1])
            if score >= 0.35:
                pairs.append((score, notes[i][0], notes[j][0]))

    lines = ["# Semantic Deduplication Report", "", f"Datum: {now_date()}", "", "| Score | Notiz A | Notiz B |", "|---:|---|---|"]
    if not pairs:
        lines.append("| 0 | Keine Kandidaten | - |")
    for score, a, b in sorted(pairs, reverse=True)[:100]:
        lines.append(f"| {score:.2f} | [[{a.stem}]] | [[{b.stem}]] |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
