from pathlib import Path
from datetime import datetime
import json
import re
import subprocess
import sys

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")
AGENT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
INBOX = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox")

def now_date():
    return datetime.now().strftime("%Y-%m-%d")

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_voice_status() -> Path:
    target = ensure(VAULT / "133_VoiceLayer") / "Voice_Layer_Status_v103.md"
    target.write_text("""# Voice Layer v10.3

Status:
- Spracheingabe: vorbereitet
- Diktat-Import: aktiv
- Sprachbefehle als Text: aktiv
- Hotword: vorbereitet
- Text-to-Speech: vorbereitet

Sicherheitsregeln:
- Keine Löschaktionen.
- Kein E-Mail-Versand.
- Ausführung review-first.
""", encoding="utf-8")
    return target

def import_dictation_file(path: str) -> Path:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(str(src))
    text = src.read_text(encoding="utf-8", errors="ignore")
    target = ensure(VAULT / "135_DictationInbox") / f"{now_stamp()}_{src.stem}.md"
    target.write_text(f"""---
title: "{src.stem}"
type: dictation
source: voice
created: {now_date()}
tags:
  - voice
  - dictation
---

# {src.stem}

## Diktat

{text}

## erkannte nächste Schritte

- [ ] prüfen und strukturieren
""", encoding="utf-8")
    return target

def import_dictation_folder() -> list[str]:
    folder = INBOX / "Voice" / "Dictation"
    folder.mkdir(parents=True, exist_ok=True)
    outputs = []
    for p in sorted(folder.glob("*.txt")) + sorted(folder.glob("*.md")):
        outputs.append(str(import_dictation_file(str(p))))
    return outputs

def command_to_script(command: str):
    c = command.lower().strip()
    if "import" in c and ("ki" in c or "ai" in c or "exports" in c):
        return ("import_ai_exports.py", [])
    if "v10" in c or "personal os" in c:
        return ("run_v10_cycle.py", [])
    if "v10.1" in c:
        return ("run_v101_cycle.py", [])
    if "v10.2" in c or "gui" in c:
        return ("run_v102_cycle.py", [])
    if "v9.9" in c or "knowledge" in c:
        return ("run_v99_cycle.py", [])
    if "rag" in c or "frage" in c:
        q = command.split(":", 1)[1].strip() if ":" in command else command
        return ("rag_answer.py", [q])
    if "prüfung" in c or "gate" in c:
        return ("production_ready_gate_v96.py", [])
    if "pfad" in c:
        return ("check_paths_v9.py", [])
    return (None, [])

def route_voice_command(command: str, execute: bool = False) -> Path:
    target = ensure(VAULT / "134_VoiceCommands") / f"{now_stamp()}_voice-command.md"
    script, args = command_to_script(command)
    lines = [
        "# Voice Command v10.3",
        "",
        f"Zeit: {now_stamp()}",
        f"Befehl: `{command}`",
        "",
        "## Interpretation",
        "",
        f"- Script: `{script or 'unbekannt'}`",
        f"- Argumente: `{args}`",
        f"- Ausführen: `{execute}`",
        "",
    ]
    if script and execute:
        p = AGENT / "scripts" / script
        if p.exists():
            result = subprocess.run([sys.executable, str(p), *args], cwd=str(AGENT), capture_output=True, text=True)
            lines += ["## Ausgabe", "", "```text", (result.stdout + "\n" + result.stderr)[-8000:], "```"]
        else:
            lines += ["## Fehler", "", f"Script nicht gefunden: `{p}`"]
    else:
        lines += ["## Review", "", "- Befehl wurde interpretiert, aber nicht ausgeführt.", "- Zur Ausführung `execute=True` verwenden."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

# === DEPRECATED (Voice Control v20) =============================
# Dieses Modul ist abgeloest durch das konsolidierte Paket secondbrain.voice.
# Nutze: from secondbrain.voice import VoiceController, VoiceConfig
# Belassen, weil noch von Launchern/Skripten referenziert. Nicht erweitern.
# Siehe docs/VOICE_CONTROL_v20.md
# ===============================================================
