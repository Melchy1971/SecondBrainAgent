from pathlib import Path
from datetime import datetime

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def write_v95_control_center() -> Path:
    target = VAULT / "98_V95ControlCenter" / "SecondBrain_v9_5_Control_Center.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    modules = [
        ("Vector RAG", "aktiv"),
        ("Ollama RAG", "aktiv wenn Ollama läuft"),
        ("Meeting Transcription", "vorbereitet"),
        ("Calendar Connectors", "vorbereitet"),
        ("Email Connectors", "vorbereitet"),
        ("Web Frontend", "Scaffold"),
        ("Realtime Event Bus", "aktiv"),
        ("Autonomous Agents", "review-first vorbereitet"),
        ("Mobile Bridge", "vorbereitet"),
        ("Copilot", "vorbereitet"),
    ]
    lines = ["# SecondBrain OS v9.5 Control Center", "", f"Aktualisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "", "| Modul | Status |", "|---|---|"]
    for m, s in modules:
        lines.append(f"| {m} | {s} |")
    lines += ["", "## Betriebsroutine", "", "1. Import AI Exports", "2. Build Vector RAG Index", "3. RAG Fragen stellen", "4. v9.5 Cycle", "5. Control Center prüfen"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
