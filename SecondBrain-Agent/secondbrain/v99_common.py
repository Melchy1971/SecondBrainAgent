from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import re

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def now_date():
    return datetime.now().strftime("%Y-%m-%d")

def now_dt():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def iter_notes(vault: Path = VAULT):
    return [p for p in vault.rglob("*.md") if ".obsidian" not in p.parts and "99_System" not in p.parts]

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def tags(text: str):
    return sorted(set(re.findall(r"#([A-Za-z0-9ÄÖÜäöüß_-]+)", text)))

def links(text: str):
    return re.findall(r"\[\[([^\]]+)\]\]", text)

def tasks(text: str):
    return re.findall(r"^\s*-\s\[[ xX]\]\s.+$", text, flags=re.MULTILINE)

def frontmatter_value(text: str, key: str):
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    m = re.search(pattern, text, flags=re.MULTILINE)
    return m.group(1).strip().strip('"') if m else ""

def source_of(text: str, path: Path):
    src = frontmatter_value(text, "source")
    if src:
        return src
    parts = set(path.parts)
    for candidate in ["ChatGPT", "Gemini", "Perplexity", "Claude"]:
        if candidate in parts:
            return candidate.lower()
    return "vault"

def note_type(text: str):
    return frontmatter_value(text, "type") or "note"

def stem_id(path: Path):
    return path.stem.replace("|", "-")
