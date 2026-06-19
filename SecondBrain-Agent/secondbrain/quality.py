from pathlib import Path
from .utils import now_date, now_datetime
from .vault_scan import iter_markdown, read_note, extract_tags, note_type

def has_frontmatter(text: str) -> bool:
    return text.strip().startswith("---")

def has_title(text: str) -> bool:
    return any(line.strip().startswith("title:") for line in text.splitlines()[:30])

def quality_report(settings: dict) -> dict:
    vault = Path(settings["vault_path"])
    notes = list(iter_markdown(vault))
    total = len(notes)
    with_fm = 0
    missing_title = []
    missing_type = []
    missing_tags = []
    empty = []
    large = []

    for note in notes:
        text = read_note(note)
        if has_frontmatter(text):
            with_fm += 1
        if not has_title(text):
            missing_title.append(note)
        if not note_type(text):
            missing_type.append(note)
        if not extract_tags(text):
            missing_tags.append(note)
        if len(text.strip()) < 20:
            empty.append(note)
        if note.stat().st_size > 250 * 1024:
            large.append(note)

    return {
        "total": total,
        "frontmatter_ratio": (with_fm / total) if total else 1,
        "missing_title": missing_title,
        "missing_type": missing_type,
        "missing_tags": missing_tags,
        "empty": empty,
        "large": large,
    }

def write_quality_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "quality"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_quality-report.md"
    r = quality_report(settings)

    lines = [
        f"# Quality Report {now_datetime()}",
        "",
        "## Kennzahlen",
        "",
        f"- Markdown-Dateien: {r['total']}",
        f"- Frontmatter-Quote: {r['frontmatter_ratio']:.2%}",
        f"- Fehlender Titel: {len(r['missing_title'])}",
        f"- Fehlender Typ: {len(r['missing_type'])}",
        f"- Fehlende Tags: {len(r['missing_tags'])}",
        f"- Leere/kleine Notizen: {len(r['empty'])}",
        f"- Große Notizen >250 KB: {len(r['large'])}",
        "",
        "## Findings",
        ""
    ]

    for label, items in [
        ("Fehlender Titel", r["missing_title"]),
        ("Fehlender Typ", r["missing_type"]),
        ("Fehlende Tags", r["missing_tags"]),
        ("Leere Notizen", r["empty"]),
        ("Große Notizen", r["large"]),
    ]:
        lines.append(f"### {label}")
        if not items:
            lines.append("- Keine")
        else:
            for p in items[:100]:
                lines.append(f"- [[{p.stem}]]")
        lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

def quality_gate(settings: dict) -> tuple[bool, list[str]]:
    r = quality_report(settings)
    issues = []
    if r["frontmatter_ratio"] < 0.75:
        issues.append("Frontmatter-Quote unter 75%")
    if len(r["empty"]) > 0:
        issues.append("Leere/zu kleine Notizen vorhanden")
    if len(r["missing_title"]) > 50:
        issues.append("Zu viele Notizen ohne Titel")
    return (len(issues) == 0, issues)
