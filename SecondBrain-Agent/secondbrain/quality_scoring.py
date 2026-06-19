from pathlib import Path
from .utils import now_date
from .vault_scan import iter_markdown, read_note, extract_tags, extract_links, note_type

def score_note(text: str) -> int:
    score = 0
    if text.strip().startswith("---"):
        score += 20
    if "title:" in text[:500]:
        score += 10
    if note_type(text):
        score += 10
    if extract_tags(text):
        score += 15
    if extract_links(text):
        score += 15
    if len(text.strip()) > 500:
        score += 15
    if "# " in text:
        score += 15
    return min(score, 100)

def write_quality_scores(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "40_QualityScores"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{now_date()}_quality-scores.md"

    rows = []
    for note in iter_markdown(vault):
        if "99_System" in note.parts:
            continue
        score = score_note(read_note(note))
        rows.append((score, note.stem))

    lines = ["# Knowledge Quality Scores", "", f"Datum: {now_date()}", "", "| Score | Notiz |", "|---:|---|"]
    for score, stem in sorted(rows):
        lines.append(f"| {score} | [[{stem}]] |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
