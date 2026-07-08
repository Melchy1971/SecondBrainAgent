from pathlib import Path
from .v99_common import VAULT, iter_notes, read, tags, links, now_date, ensure

def score_note(text: str):
    score = 0
    if text.strip().startswith("---"):
        score += 20
    if len(text.strip()) >= 250:
        score += 20
    if tags(text):
        score += 20
    if links(text):
        score += 20
    if "##" in text:
        score += 20
    return score

def write_quality_report(vault: Path = VAULT) -> Path:
    target = ensure(vault / "117_KnowledgeQuality") / f"{now_date()}_knowledge-quality.md"
    rows = []
    for p in iter_notes(vault):
        text = read(p)
        score = score_note(text)
        if score < 80:
            missing = []
            if not text.strip().startswith("---"): missing.append("Frontmatter")
            if len(text.strip()) < 250: missing.append("Inhalt")
            if not tags(text): missing.append("Tags")
            if not links(text): missing.append("Links")
            if "##" not in text: missing.append("Struktur")
            rows.append((score, p.stem, missing))
    lines = ["# Knowledge Quality v9.9", "", f"Datum: {now_date()}", "", "| Score | Notiz | Fehlend |", "|---:|---|---|"]
    for score, stem, missing in sorted(rows)[:200]:
        lines.append(f"| {score} | [[{stem}]] | {', '.join(missing)} |")
    if not rows:
        lines.append("| 100 | alle geprüften Notizen ausreichend | - |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
