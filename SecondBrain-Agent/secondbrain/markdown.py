from pathlib import Path
from .utils import now_date, slugify, ensure_unique_path

TYPE_TO_FOLDER = {
    "inbox": "inbox",
    "project": "projects",
    "knowledge": "knowledge",
    "person": "people",
    "task": "tasks",
    "source": "sources",
}

def title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip("# ").strip()
        if line:
            return line[:90]
    return fallback

def backlinks_for(tags: list[str]) -> str:
    if not tags:
        return "- Keine"
    lines = []
    for tag in tags:
        label = tag.replace("-", " ").title()
        lines.append(f"- [[{label}]]")
    return "\n".join(lines)

def build_markdown(title, note_type, source_file, provider, text, tags):
    tag_lines = "\n".join([f"  - {t}" for t in tags]) if tags else "  - inbox"
    links = backlinks_for(tags)

    if note_type == "task":
        tasks = []
        for line in text.splitlines():
            l = line.strip()
            if not l:
                continue
            if "aufgabe:" in l.lower():
                tasks.append("- [ ] " + l.split(":", 1)[-1].strip())
            elif l.startswith("- [ ]"):
                tasks.append(l)
        if not tasks:
            tasks = ["- [ ] Inhalt prüfen und einordnen"]
        body = "# Aufgaben\n\n" + "\n".join(tasks) + "\n\n# Kontext\n\n" + text
    elif note_type == "project":
        body = "# Ziel\n\n" + text[:500] + "\n\n# Kontext\n\n" + text + "\n\n# Aufgaben\n\n- [ ] Status prüfen\n- [ ] nächste Schritte definieren\n\n# Entscheidungen\n\n# Risiken\n\n# Verknüpfungen\n\n" + links
    elif note_type == "source":
        body = "# Quelle\n\nProvider: " + provider + "\n\n# Kernaussagen\n\n" + text + "\n\n# Verknüpfungen\n\n" + links
    else:
        body = "# Zusammenfassung\n\n" + text[:700] + "\n\n# Inhalt\n\n" + text + "\n\n# Verknüpfungen\n\n" + links

    return f"""---
title: "{title}"
type: {note_type}
status: imported
created: {now_date()}
source_file: "{source_file}"
provider: "{provider}"
tags:
{tag_lines}
---

{body}
"""

def write_note(settings, note_type, provider, source_path: Path, text, tags) -> Path:
    vault = Path(settings["vault_path"])
    folders = settings.get("vault_folders", {})
    folder_key = TYPE_TO_FOLDER.get(note_type, "inbox")
    folder = folders.get(folder_key, "00_Inbox")
    target_dir = vault / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    title = title_from_text(text, source_path.stem)
    filename = f"{now_date()}_{slugify(title)}.md"
    target = ensure_unique_path(target_dir / filename)
    target.write_text(build_markdown(title, note_type, str(source_path), provider, text, tags), encoding="utf-8")
    return target
