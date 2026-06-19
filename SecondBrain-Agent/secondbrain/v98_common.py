from pathlib import Path
from datetime import datetime
import re
from collections import Counter, defaultdict

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

def open_tasks(text: str):
    return re.findall(r"^\s*-\s\[\s\]\s.+$", text, flags=re.MULTILINE)

def done_tasks(text: str):
    return re.findall(r"^\s*-\s\[[xX]\]\s.+$", text, flags=re.MULTILINE)

def links(text: str):
    return re.findall(r"\[\[([^\]]+)\]\]", text)

def tags(text: str):
    return sorted(set(re.findall(r"#([A-Za-z0-9ÄÖÜäöüß_-]+)", text)))

def signals(text: str):
    low = text.lower()
    return {
        "risk": low.count("risiko") + low.count("blockiert") + low.count("blocked") + low.count("fail"),
        "decision": low.count("entscheidung") + low.count("beschluss") + low.count("festlegung"),
        "meeting": low.count("meeting") + low.count("protokoll") + low.count("agenda"),
        "project": low.count("projekt") + low.count("roadmap") + low.count("sprint"),
        "process": low.count("prozess") + low.count("workflow") + low.count("schnittstelle"),
        "research": low.count("recherche") + low.count("quelle") + low.count("wissenslücke"),
    }

def note_bucket(path: Path, text: str):
    low = text.lower()
    parts = set(path.parts)
    if "01_Projekte" in parts or "type: project" in low:
        return "project"
    if "Meeting" in path.stem or "meeting" in low or "protokoll" in low:
        return "meeting"
    if "entscheidung" in low or "decision" in low:
        return "decision"
    if "prozess" in low or "workflow" in low:
        return "process"
    if "quelle" in low or "recherche" in low:
        return "research"
    return "knowledge"
