from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v101_cycle.py")
    target = VAULT / "132_JarvisControlCenterGUI" / "Jarvis_Control_Center_GUI.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("""# Jarvis Control Center GUI v10.2

Status: aktiv

Start:

```powershell
cd H:\\SecondBrainAgent\\SecondBrain-Agent
python scripts\\start_gui.py
```

URL:

```text
http://127.0.0.1:8850
```

Funktionen:
- Status
- Importe
- v10/v10.1 Cycle
- RAG
- Release Gate
- Regression Tests
- Logs
- Dashboard-Pfade
""", encoding="utf-8")
    print("SecondBrain v10.2 GUI Cycle abgeschlossen:")
    print("-", target)
