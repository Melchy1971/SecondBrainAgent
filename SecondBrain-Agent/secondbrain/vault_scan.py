from pathlib import Path
import re

def iter_markdown(vault: Path):
    for p in vault.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        yield p

def read_note(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def frontmatter_value(text: str, key: str) -> str:
    pattern = rf"^{key}:\s*(.+)$"
    for line in text.splitlines():
        m = re.match(pattern, line.strip())
        if m:
            return m.group(1).strip().strip('"')
    return ""

def note_type(text: str) -> str:
    return frontmatter_value(text, "type")

def extract_tags(text: str) -> list[str]:
    tags = []
    in_tags = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "tags:":
            in_tags = True
            continue
        if in_tags:
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                break
    return tags

def extract_tasks(text: str) -> list[str]:
    tasks = []
    for line in text.splitlines():
        l = line.strip()
        if l.startswith("- [ ]") or l.startswith("- [x]") or l.startswith("- [X]"):
            tasks.append(l)
    return tasks

def extract_links(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", text)

def word_tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-zÄÖÜäöüß0-9]{4,}", text.lower()))
