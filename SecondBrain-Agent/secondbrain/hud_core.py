"""Neutrales Kernmodul fuer die GUI (Phase 2).

Enthaelt die GUI-unabhaengige Logik, die frueher in gui_backend_v102.py lag:
Pfade, Logging, Skript-Runner, Systemstatus, Dashboard-Links. Sowohl das HUD
(jarvis_hud_server) als auch die alte Control-Center-GUI (gui_backend_v102)
importieren von hier - eine einzige Quelle der Wahrheit, kein Frontend, das von
einem anderen Frontend abhaengt.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")
LOG_DIR = ROOT / "logs"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_event(event_type: str, payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {"time": now(), "type": event_type, "payload": payload}
    with (LOG_DIR / "jarvis_gui.log").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_script(script: str, *args: str) -> dict:
    p = ROOT / "scripts" / script
    if not p.exists():
        return {"ok": False, "script": script, "output": f"Script nicht gefunden: {p}"}
    result = subprocess.run(
        [sys.executable, str(p), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    output = (result.stdout + "\n" + result.stderr)[-12000:]
    log_event("script.run", {"script": script, "ok": result.returncode == 0})
    return {"ok": result.returncode == 0, "script": script, "output": output}


def system_status() -> dict:
    return {
        "time": now(),
        "root": str(ROOT),
        "vault": str(VAULT),
        "inbox": str(INBOX),
        "root_exists": ROOT.exists(),
        "vault_exists": VAULT.exists(),
        "inbox_exists": INBOX.exists(),
        "python": sys.version,
        "markdown_files": len(list(VAULT.rglob("*.md"))) if VAULT.exists() else 0,
        "log_exists": (LOG_DIR / "jarvis_gui.log").exists(),
    }


def latest_file(folder: Path) -> str:
    if not folder.exists():
        return ""
    files = sorted(folder.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
    return str(files[0]) if files else ""


def dashboard_links() -> dict:
    return {
        "Command Center v10": str(VAULT / "126_CommandCenter" / "SecondBrain_Command_Center_v10.md"),
        "Jarvis Copilot": latest_file(VAULT / "125_JarvisCopilot"),
        "Life Dashboard": str(VAULT / "120_LifeDashboard" / "Life_Dashboard_v10.md"),
        "Knowledge Intelligence": str(VAULT / "119_KnowledgeIntelligenceDashboard" / "Knowledge_Intelligence_Dashboard_v99.md"),
        "v9.5 Control Center": str(VAULT / "98_V95ControlCenter" / "SecondBrain_v9_5_Control_Center.md"),
        "Release Gates": str(VAULT / "95_Operations" / "ReleaseGates"),
    }
