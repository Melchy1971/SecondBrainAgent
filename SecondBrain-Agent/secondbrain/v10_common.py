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

def open_tasks(text: str):
    return re.findall(r"^\s*-\s\[\s\]\s.+$", text, flags=re.MULTILINE)

def done_tasks(text: str):
    return re.findall(r"^\s*-\s\[[xX]\]\s.+$", text, flags=re.MULTILINE)

def tags(text: str):
    return sorted(set(re.findall(r"#([A-Za-z0-9ÄÖÜäöüß_-]+)", text)))

def domain_of(path: Path, text: str) -> str:
    low = (str(path) + "\n" + text).lower()
    rules = {
        "Beruf": ["sap", "telekom", "prozess", "management", "arbeit", "crm"],
        "Projekte": ["projekt", "secondbrain", "jarvis", "wissensdatenbank", "release"],
        "Gesundheit": ["gesundheit", "diabetes", "training", "gewicht", "hba1c", "ozempic"],
        "Finanzen": ["finanzen", "rechnung", "kosten", "budget", "steuer"],
        "Lernen": ["lernen", "kurs", "skill", "ki", "python"],
        "Reisen": ["reise", "urlaub", "hotel", "flug", "madeira"],
        "Verein": ["ttc", "verein", "tischtennis", "turnier", "zaberfeld"],
        "Privat": ["privat", "haus", "familie", "garten", "pool"],
    }
    scores = {d: sum(low.count(k) for k in keys) for d, keys in rules.items()}
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] else "Unklassifiziert"

def signals(text: str):
    low = text.lower()
    return {
        "risk": low.count("risiko") + low.count("blockiert") + low.count("blocked") + low.count("fail"),
        "decision": low.count("entscheidung") + low.count("beschluss") + low.count("festlegung"),
        "meeting": low.count("meeting") + low.count("protokoll") + low.count("agenda"),
        "project": low.count("projekt") + low.count("roadmap") + low.count("sprint"),
        "goal": low.count("ziel") + low.count("kpi") + low.count("fortschritt"),
    }
