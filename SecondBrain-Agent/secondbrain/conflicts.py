from pathlib import Path
import re
from collections import defaultdict
from .utils import now_date, now_datetime
from .vault_scan import iter_markdown

CONFLICT_PATTERNS = [
    "conflict",
    "konflikt",
    "sync-conflict",
    "sync conflict",
    "(1).md",
    "kopie",
    "copy",
]

def detect_conflicts(settings: dict) -> list[Path]:
    vault = Path(settings["vault_path"])
    conflicts = []
    by_stem = defaultdict(list)

    for note in iter_markdown(vault):
        name = note.name.lower()
        if any(p in name for p in CONFLICT_PATTERNS):
            conflicts.append(note)
        by_stem[note.stem.lower()].append(note)

    for stem, files in by_stem.items():
        if len(files) > 1:
            conflicts.extend(files)

    seen = []
    out = []
    for p in conflicts:
        if p not in seen:
            seen.append(p)
            out.append(p)
    return out

def write_conflict_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "conflicts"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_conflict-report.md"
    conflicts = detect_conflicts(settings)

    lines = [
        f"# Conflict Report {now_datetime()}",
        "",
        f"Konflikte: {len(conflicts)}",
        "",
    ]

    if not conflicts:
        lines.append("- Keine Konflikte erkannt.")
    else:
        for p in conflicts:
            lines.append(f"- `{p.relative_to(vault)}`")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target
