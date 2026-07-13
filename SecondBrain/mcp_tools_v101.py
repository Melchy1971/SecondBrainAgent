from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import json

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

SAFE_NAME = re.compile(r"^[A-Za-z0-9ÄÖÜäöüß_\- .()]+$")
SAFE_FOLDER = re.compile(r"^[A-Za-z0-9ÄÖÜäöüß_\- ./\\]+$")

def now_date():
    return datetime.now().strftime("%Y-%m-%d")

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def sanitize_title(title: str) -> str:
    title = title.strip().replace("/", "-").replace("\\", "-").replace(":", "-")
    title = re.sub(r"\s+", " ", title)
    if not title:
        title = f"Notiz_{now_stamp()}"
    if not SAFE_NAME.match(title):
        title = re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_\- .()]", "-", title)
    return title[:120]

def safe_folder(folder: str) -> Path:
    folder = folder.strip().strip("/\\") or "00_Inbox"
    if not SAFE_FOLDER.match(folder):
        raise ValueError("Ungültiger Ordner.")
    target = (VAULT / folder).resolve()
    if VAULT.resolve() not in target.parents and target != VAULT.resolve():
        raise ValueError("Pfad außerhalb des Vaults blockiert.")
    target.mkdir(parents=True, exist_ok=True)
    return target

def safe_path(path: str) -> Path:
    p = Path(path).resolve()
    if VAULT.resolve() not in p.parents and p != VAULT.resolve():
        raise ValueError("Pfad außerhalb des Vaults blockiert.")
    return p

def frontmatter(title: str, note_type: str, tags=None, source="claude-mcp") -> str:
    tags = tags or ["inbox"]
    tag_lines = "\n".join(f"  - {t}" for t in tags)
    return f"""---
title: "{title.replace('"', "'")}"
type: {note_type}
source: {source}
created: {now_date()}
tags:
{tag_lines}
---

"""

def create_note(title: str, folder: str = "00_Inbox", content: str = "", note_type: str = "note", tags=None) -> str:
    title = sanitize_title(title)
    target_dir = safe_folder(folder)
    target = target_dir / f"{title}.md"
    if target.exists():
        target = target_dir / f"{title}_{now_stamp()}.md"
    md = frontmatter(title, note_type, tags) + f"# {title}\n\n{content.strip()}\n"
    target.write_text(md, encoding="utf-8")
    return str(target)

def update_note(path: str, content: str, mode: str = "append") -> str:
    p = safe_path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if mode == "replace":
        p.write_text(content, encoding="utf-8")
    else:
        with p.open("a", encoding="utf-8") as f:
            f.write("\n\n")
            f.write(content.strip())
            f.write("\n")
    return str(p)

def read_note(path: str, limit: int = 60000) -> str:
    p = safe_path(path)
    if not p.exists():
        return "Datei nicht gefunden."
    return p.read_text(encoding="utf-8", errors="ignore")[:limit]

def search_notes(query: str, limit: int = 20) -> list[dict]:
    q = query.lower().strip()
    if not q:
        return []
    results = []
    for p in VAULT.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hay = (p.stem + "\n" + text).lower()
        if q in hay:
            results.append({"title": p.stem, "path": str(p), "preview": text[:600]})
            if len(results) >= limit:
                break
    return results

def create_project(name: str, description: str = "") -> str:
    name = sanitize_title(name)
    folder = safe_folder(f"01_Projekte/{name}")
    files = {
        "00_Projektübersicht.md": f"# {name}\n\n## Ziel\n\n{description or 'Noch offen.'}\n\n## Status\n\noffen\n\n## Nächste Schritte\n\n- [ ] Ziel schärfen\n- [ ] Aufgaben definieren\n",
        "01_Aufgaben.md": f"# {name} Aufgaben\n\n- [ ] Erste Aufgabe definieren\n",
        "02_Entscheidungen.md": f"# {name} Entscheidungen\n\n| Datum | Entscheidung | Annahme | Risiko | Ergebnis |\n|---|---|---|---|---|\n",
        "03_Meetings.md": f"# {name} Meetings\n\n",
        "04_Notizen.md": f"# {name} Notizen\n\n",
    }
    for fname, body in files.items():
        p = folder / fname
        if not p.exists():
            p.write_text(frontmatter(fname.replace(".md",""), "project_file", ["project"]) + body, encoding="utf-8")
    return str(folder)

def create_task(title: str, project: str = "", content: str = "") -> str:
    body = f"## Aufgabe\n\n- [ ] {content or title}\n\n## Projekt\n\n{project}\n\n## Status\n\noffen\n"
    return create_note(title, "04_Tasks", body, "task", ["task"])

def create_meeting(title: str, project: str = "", content: str = "") -> str:
    body = f"## Projekt\n\n{project}\n\n## Zusammenfassung\n\n{content}\n\n## Aufgaben\n\n## Entscheidungen\n\n## Risiken\n\n## Follow-up\n"
    return create_note(title, "108_MeetingAgent", body, "meeting", ["meeting"])

def create_decision(title: str, project: str = "", content: str = "") -> str:
    body = f"## Projekt\n\n{project}\n\n## Entscheidung\n\n{content}\n\n## Annahmen\n\n## Alternativen\n\n## Risiken\n\n## Ergebnis\n"
    return create_note(title, "110_DecisionAgent", body, "decision", ["decision"])

def list_projects() -> list[dict]:
    folder = VAULT / "01_Projekte"
    if not folder.exists():
        return []
    return [{"name": p.name, "path": str(p)} for p in folder.iterdir() if p.is_dir()]

def get_dashboard(name: str = "command_center") -> str:
    mapping = {
        "command_center": VAULT / "126_CommandCenter" / "SecondBrain_Command_Center_v10.md",
        "life": VAULT / "120_LifeDashboard" / "Life_Dashboard_v10.md",
        "knowledge": VAULT / "119_KnowledgeIntelligenceDashboard" / "Knowledge_Intelligence_Dashboard_v99.md",
        "jarvis": VAULT / "125_JarvisCopilot",
        "control_v95": VAULT / "98_V95ControlCenter" / "SecondBrain_v9_5_Control_Center.md",
    }
    p = mapping.get(name, mapping["command_center"])
    if p.is_dir():
        files = sorted(p.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        p = files[0] if files else p
    if not p.exists() or p.is_dir():
        return "Dashboard nicht gefunden."
    return p.read_text(encoding="utf-8", errors="ignore")[:50000]

def query_knowledge_graph(query: str) -> list[dict]:
    rel = VAULT / "99_System" / "relationships" / "relationships.json"
    if not rel.exists():
        return []
    data = json.loads(rel.read_text(encoding="utf-8"))
    q = query.lower()
    return [e for e in data if q in str(e).lower()][:50]
