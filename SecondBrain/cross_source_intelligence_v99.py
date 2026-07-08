from pathlib import Path
from collections import defaultdict, Counter
from .v99_common import VAULT, iter_notes, read, source_of, tags, now_date, ensure

def write_cross_source_report(vault: Path = VAULT) -> Path:
    target = ensure(vault / "118_CrossSourceIntelligence") / f"{now_date()}_cross-source-intelligence.md"
    by_source = defaultdict(list)
    tag_by_source = defaultdict(Counter)

    for p in iter_notes(vault):
        text = read(p)
        src = source_of(text, p)
        by_source[src].append(p.stem)
        tag_by_source[src].update(tags(text))

    all_tags = defaultdict(set)
    for src, counter in tag_by_source.items():
        for tag in counter:
            all_tags[tag].add(src)

    shared = {tag: srcs for tag, srcs in all_tags.items() if len(srcs) > 1}

    lines = ["# Cross Source Intelligence v9.9", "", f"Datum: {now_date()}", "", "## Quellen", "", "| Quelle | Notizen |", "|---|---:|"]
    for src, notes in sorted(by_source.items()):
        lines.append(f"| {src} | {len(notes)} |")
    lines += ["", "## Quellenübergreifende Tags", ""]
    if shared:
        for tag, srcs in sorted(shared.items(), key=lambda x: len(x[1]), reverse=True)[:100]:
            lines.append(f"- #{tag}: {', '.join(sorted(srcs))}")
    else:
        lines.append("- Keine.")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
