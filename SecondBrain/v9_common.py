from pathlib import Path
import re
from collections import Counter
from datetime import datetime

VAULT_DEFAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def now_date():
    return datetime.now().strftime("%Y-%m-%d")

def now_dt():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def iter_md(vault: Path):
    if not vault.exists():
        return []
    return [p for p in vault.rglob("*.md") if ".obsidian" not in p.parts]

def read(p: Path):
    return p.read_text(encoding="utf-8", errors="ignore")

def tags(text: str):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- ") and len(s) < 60:
            val = s[2:].strip()
            if val and " " not in val and not val.startswith("["):
                out.append(val.replace("#",""))
    out += re.findall(r"#([A-Za-z0-9ÄÖÜäöüß_-]+)", text)
    return sorted(set(out))

def tasks(text: str):
    return re.findall(r"^\s*-\s\[[ xX]\]\s.+$", text, flags=re.MULTILINE)

def links(text: str):
    return re.findall(r"\[\[([^\]]+)\]\]", text)

def slug(value: str, max_len=90):
    value = value.strip() or "Ohne_Titel"
    value = re.sub(r"[^\w\sÄÖÜäöüß.-]", "-", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    return value[:max_len].strip("._-") or "Ohne_Titel"

def ensure(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path
