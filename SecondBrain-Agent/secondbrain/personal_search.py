from pathlib import Path
from .utils import now_date, slugify
from .vault_scan import iter_markdown, read_note

def personal_search(settings: dict, query: str) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "54_PersonalSearch"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_search_{slugify(query)}.md"

    terms = [t.lower() for t in query.split() if len(t) >= 3]
    hits = []
    for note in iter_markdown(vault):
        text = read_note(note).lower()
        score = sum(text.count(t) for t in terms)
        if score:
            hits.append((score, note.stem))

    lines = [f"# Personal Search: {query}", "", f"Datum: {now_date()}", "", "| Score | Treffer |", "|---:|---|"]
    for score, stem in sorted(hits, reverse=True)[:100]:
        lines.append(f"| {score} | [[{stem}]] |")
    if not hits:
        lines.append("| 0 | keine Treffer |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
