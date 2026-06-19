from pathlib import Path
import subprocess
import re
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("secondbrain")

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
AGENT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")

SAFE_FOLDER_RE = re.compile(r"^[A-Za-z0-9ÄÖÜäöüß_\- ./\\]+$")
SAFE_TITLE_RE = re.compile(r"^[A-Za-z0-9ÄÖÜäöüß_\- .()]+$")

def _safe_title(title: str) -> str:
    title = title.strip().replace("/", "-").replace("\\", "-").replace(":", "-")
    title = re.sub(r"\s+", " ", title)
    if not title:
        title = f"Notiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not SAFE_TITLE_RE.match(title):
        title = re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_\- .()]", "-", title)
    return title[:120]

def _safe_folder(folder: str) -> Path:
    folder = folder.strip().strip("/\\")
    if not folder:
        folder = "00_Inbox"
    if not SAFE_FOLDER_RE.match(folder):
        raise ValueError("Ungültiger Ordnername.")
    target = (VAULT / folder).resolve()
    if VAULT.resolve() not in target.parents and target != VAULT.resolve():
        raise ValueError("Pfad außerhalb des Vaults blockiert.")
    return target

def _safe_file_from_path(path: str) -> Path:
    file = Path(path).resolve()
    if VAULT.resolve() not in file.parents and file != VAULT.resolve():
        raise ValueError("Pfad außerhalb des Vaults blockiert.")
    return file

def _frontmatter(title: str, note_type: str, tags: list[str] | None = None) -> str:
    tags = tags or []
    tag_lines = "\n".join(f"  - {t}" for t in tags) if tags else "  - inbox"
    return f"""---
title: "{title}"
type: {note_type}
created: {datetime.now().strftime('%Y-%m-%d')}
source: claude-mcp
tags:
{tag_lines}
---

"""

@mcp.tool()
def create_note(title: str, folder: str = "00_Inbox", content: str = "", note_type: str = "inbox", tags: list[str] | None = None) -> str:
    """Erstellt eine neue Markdown-Notiz im Obsidian Vault."""
    safe_title = _safe_title(title)
    target_dir = _safe_folder(folder)
    target_dir.mkdir(parents=True, exist_ok=True)

    file = target_dir / f"{safe_title}.md"
    if file.exists():
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = target_dir / f"{safe_title}_{suffix}.md"

    text = _frontmatter(safe_title, note_type, tags) + f"# {safe_title}\n\n{content.strip()}\n"
    file.write_text(text, encoding="utf-8")
    return f"Notiz erstellt: {file}"

@mcp.tool()
def append_note(title: str, folder: str = "00_Inbox", content: str = "") -> str:
    """Ergänzt eine bestehende Markdown-Notiz."""
    safe_title = _safe_title(title)
    file = _safe_folder(folder) / f"{safe_title}.md"

    if not file.exists():
        return f"Datei nicht gefunden: {file}"

    with file.open("a", encoding="utf-8") as f:
        f.write("\n\n")
        f.write(content.strip())
        f.write("\n")
    return f"Notiz ergänzt: {file}"

@mcp.tool()
def read_note(path: str) -> str:
    """Liest eine Markdown-Datei aus dem Vault."""
    file = _safe_file_from_path(path)
    if not file.exists() or not file.is_file():
        return "Datei nicht gefunden."
    return file.read_text(encoding="utf-8", errors="ignore")[:50000]

@mcp.tool()
def search_notes(query: str, limit: int = 20) -> list[dict]:
    """Durchsucht Markdown-Dateien im Vault per Volltext."""
    results = []
    q = query.lower().strip()
    if not q:
        return results

    for md in VAULT.rglob("*.md"):
        if ".obsidian" in md.parts:
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if q in text.lower() or q in md.stem.lower():
            results.append({
                "title": md.stem,
                "path": str(md),
                "preview": text[:500]
            })
            if len(results) >= limit:
                break
    return results

@mcp.tool()
def create_project(title: str, content: str = "", tags: list[str] | None = None) -> str:
    """Erstellt eine Projektnotiz."""
    tags = tags or ["project"]
    body = f"""## Ziel

{content.strip()}

## Status

offen

## Aufgaben

- [ ] Nächsten Schritt definieren

## Risiken

## Entscheidungen

## Quellen
"""
    return create_note(title=title, folder="01_Projekte", content=body, note_type="project", tags=tags)

@mcp.tool()
def create_meeting(title: str, content: str = "", tags: list[str] | None = None) -> str:
    """Erstellt eine Meetingnotiz."""
    tags = tags or ["meeting"]
    body = f"""## Zusammenfassung

{content.strip()}

## Teilnehmer

## Entscheidungen

## Aufgaben

## Risiken

## Follow-up
"""
    return create_note(title=title, folder="69_MeetingIntelligence", content=body, note_type="meeting", tags=tags)

@mcp.tool()
def create_decision(title: str, content: str = "", tags: list[str] | None = None) -> str:
    """Erstellt eine Entscheidungsnotiz."""
    tags = tags or ["decision"]
    body = f"""## Entscheidung

{content.strip()}

## Annahmen

## Alternativen

## Risiken

## Ergebnis

## Lessons Learned
"""
    return create_note(title=title, folder="68_DecisionIntelligence", content=body, note_type="decision", tags=tags)

@mcp.tool()
def create_task(title: str, content: str = "", project: str = "", tags: list[str] | None = None) -> str:
    """Erstellt eine Aufgabennotiz."""
    tags = tags or ["task"]
    body = f"""## Aufgabe

- [ ] {content.strip() or title}

## Projekt

{project}

## Status

offen

## Nächster Schritt
"""
    return create_note(title=title, folder="04_Tasks", content=body, note_type="task", tags=tags)

@mcp.tool()
def create_journal(content: str, title: str = "") -> str:
    """Erstellt einen Journaleintrag für heute."""
    today = datetime.now().strftime("%Y-%m-%d")
    title = title or f"Journal_{today}"
    return create_note(title=title, folder="06_Journal", content=content, note_type="journal", tags=["journal"])

@mcp.tool()
def semantic_search(query: str) -> str:
    """Startet die Semantic Search des SecondBrain-Agent."""
    script = AGENT / "scripts" / "semantic_search.py"
    if not script.exists():
        return "semantic_search.py nicht gefunden."
    result = subprocess.run(["python", str(script), query], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def run_import() -> str:
    """Startet den Importlauf."""
    script = AGENT / "scripts" / "run_once.py"
    if not script.exists():
        return "run_once.py nicht gefunden."
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def run_os_cycle() -> str:
    """Startet den SecondBrain OS Cycle."""
    script = AGENT / "scripts" / "run_secondbrain_os_cycle.py"
    if not script.exists():
        return "run_secondbrain_os_cycle.py nicht gefunden."
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def get_today_dashboard() -> str:
    """Liest das SecondBrain OS Dashboard."""
    dashboard = VAULT / "75_SecondBrainOS" / "SecondBrain_OS_Dashboard.md"
    if not dashboard.exists():
        return "Dashboard nicht gefunden. Starte zuerst run_os_cycle()."
    return dashboard.read_text(encoding="utf-8", errors="ignore")[:30000]


@mcp.tool()
def create_project_folder(project_name: str, description: str = "") -> str:
    """Legt im Ordner 01_Projekte einen Projektordner mit Startdateien an."""
    safe_name = _safe_title(project_name)
    project_dir = VAULT / "01_Projekte" / safe_name
    project_dir.mkdir(parents=True, exist_ok=True)

    overview = project_dir / "00_Projektübersicht.md"
    tasks = project_dir / "01_Aufgaben.md"
    decisions = project_dir / "02_Entscheidungen.md"
    notes = project_dir / "03_Notizen.md"

    if not overview.exists():
        overview.write_text(
            _frontmatter(safe_name, "project", ["project"]) +
            f"""# {safe_name}

## Ziel

{description.strip() or "Noch offen."}

## Status

offen

## Kontext

## Risiken

## Nächste Schritte

- [ ] Projektziel schärfen
- [ ] erste Aufgaben definieren
- [ ] relevante Quellen verlinken

## Links

- [[01_Aufgaben]]
- [[02_Entscheidungen]]
- [[03_Notizen]]
""",
            encoding="utf-8"
        )

    if not tasks.exists():
        tasks.write_text(
            _frontmatter(f"{safe_name} Aufgaben", "task_list", ["project", "tasks"]) +
            f"""# {safe_name} Aufgaben

- [ ] Projektziel finalisieren
- [ ] Meilensteine definieren
- [ ] Risiken prüfen
""",
            encoding="utf-8"
        )

    if not decisions.exists():
        decisions.write_text(
            _frontmatter(f"{safe_name} Entscheidungen", "decision_log", ["project", "decision"]) +
            f"""# {safe_name} Entscheidungen

| Datum | Entscheidung | Annahme | Risiko | Ergebnis |
|---|---|---|---|---|
""",
            encoding="utf-8"
        )

    if not notes.exists():
        notes.write_text(
            _frontmatter(f"{safe_name} Notizen", "notes", ["project", "notes"]) +
            f"""# {safe_name} Notizen

## Sammlung

""",
            encoding="utf-8"
        )

    return f"Projektordner erstellt: {project_dir}"

@mcp.tool()
def slash_command(command: str, argument: str = "") -> str:
    """Verarbeitet einfache SecondBrain Slash-Befehle wie /plan."""
    cmd = command.strip().lower()

    if cmd == "/plan":
        if not argument.strip():
            return "Projektname fehlt. Bitte erneut mit Projektname ausführen, z. B. /plan Jarvis."
        return create_project_folder(argument.strip())

    return f"Unbekannter Befehl: {command}"


@mcp.tool()
def run_v9_cycle() -> str:
    """Startet den SecondBrain v9 Cycle."""
    script = AGENT / "scripts" / "run_v9_cycle.py"
    if not script.exists():
        return "run_v9_cycle.py nicht gefunden."
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def run_ai_imports() -> str:
    """Importiert ChatGPT, Gemini und Perplexity Exporte aus den Inbox-Ordnern."""
    script = AGENT / "scripts" / "import_ai_exports.py"
    if not script.exists():
        return "import_ai_exports.py nicht gefunden."
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def get_control_center() -> str:
    """Liest das SecondBrain OS Control Center v9."""
    file = VAULT / "87_ControlCenter" / "SecondBrain_OS_Control_Center.md"
    if not file.exists():
        return "Control Center nicht gefunden. Starte zuerst run_v9_cycle()."
    return file.read_text(encoding="utf-8", errors="ignore")[:30000]


@mcp.tool()
def run_v95_cycle() -> str:
    """Startet den SecondBrain v9.5 Cycle."""
    script = AGENT / "scripts" / "run_v95_cycle.py"
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def build_vector_rag() -> str:
    """Baut den lokalen Vector-RAG-Index."""
    script = AGENT / "scripts" / "build_vector_rag.py"
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def rag_search(question: str) -> str:
    """Führt lokale RAG-Suche aus."""
    script = AGENT / "scripts" / "rag_search.py"
    result = subprocess.run(["python", str(script), question], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def rag_answer(question: str) -> str:
    """Beantwortet eine Frage über Vault-Kontext mit Ollama."""
    script = AGENT / "scripts" / "rag_answer.py"
    result = subprocess.run(["python", str(script), question], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]


@mcp.tool()
def production_ready_gate_v96() -> str:
    """Führt das Production Ready Gate v9.6 aus."""
    script = AGENT / "scripts" / "production_ready_gate_v96.py"
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

@mcp.tool()
def update_preflight_v96() -> str:
    """Erstellt Backup, Installer Check, Settings Report und Production Gate."""
    script = AGENT / "scripts" / "update_preflight_v96.py"
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]


@mcp.tool()
def run_v97_cycle() -> str:
    """Startet den SecondBrain v9.7 AI Copilot Cycle."""
    script = AGENT / "scripts" / "run_v97_cycle.py"
    result = subprocess.run(["python", str(script)], cwd=str(AGENT), capture_output=True, text=True)
    return (result.stdout + "\n" + result.stderr)[-4000:]

if __name__ == "__main__":
    mcp.run()
