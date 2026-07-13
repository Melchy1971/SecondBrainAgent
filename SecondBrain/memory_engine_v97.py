from pathlib import Path
from collections import Counter
from .v97_common import VAULT, iter_notes, read, tags, links, open_tasks, signals, now_date, ensure

def build_memory_profile(vault: Path = VAULT) -> Path:
    target = ensure(vault / "100_MemoryEngine") / "Memory_Engine_Profile.md"
    tag_counter = Counter()
    link_counter = Counter()
    signal_counter = Counter()
    task_count = 0
    recent = []

    for p in iter_notes(vault):
        text = read(p)
        tag_counter.update(tags(text))
        link_counter.update(links(text))
        signal_counter.update(signals(text))
        task_count += len(open_tasks(text))
        try:
            recent.append((p.stat().st_mtime, p.stem))
        except Exception:
            pass

    recent = sorted(recent, reverse=True)[:30]
    lines = [
        "# Memory Engine Profile v9.7",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "## Kurzzeitgedächtnis",
        "",
    ]
    for _, stem in recent:
        lines.append(f"- [[{stem}]]")
    lines += ["", "## Langzeit-Signale", ""]
    for k, v in signal_counter.most_common():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Häufige Tags", ""]
    for k, v in tag_counter.most_common(30):
        lines.append(f"- #{k}: {v}")
    lines += ["", "## Häufige Verknüpfungen", ""]
    for k, v in link_counter.most_common(30):
        lines.append(f"- [[{k}]]: {v}")
    lines += ["", "## Offene Aufgaben", "", f"- Gesamt: {task_count}"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
