from pathlib import Path
from datetime import datetime
from collections import Counter
import re

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
AGENT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")

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

def open_tasks(text: str):
    return [t for t in tasks(text) if "[ ]" in t]

def signals(text: str):
    low = text.lower()
    return {
        "risk": low.count("risiko") + low.count("blockiert") + low.count("blocked"),
        "decision": low.count("entscheidung") + low.count("beschluss"),
        "meeting": low.count("meeting") + low.count("protokoll"),
        "project": low.count("projekt") + low.count("roadmap"),
        "learning": low.count("lernen") + low.count("kurs") + low.count("skill"),
    }
