from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.service_config import load_service_config

def run(script):
    print(f"[{datetime.now()}] Starte {script}")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    cfg = load_service_config(PROJECT_ROOT)
    import_minutes = int(cfg.get("import_interval_minutes", 30))
    intelligence_minutes = int(cfg.get("intelligence_interval_minutes", 120))
    governance_minutes = int(cfg.get("governance_interval_minutes", 240))

    next_import = datetime.now()
    next_intel = datetime.now()
    next_gov = datetime.now()

    print("SecondBrain Scheduler gestartet. Abbruch: STRG+C")

    while True:
        now = datetime.now()

        if now >= next_import:
            run("run_once.py")
            next_import = now + timedelta(minutes=import_minutes)

        if now >= next_intel:
            run("run_intelligence_cycle.py")
            next_intel = now + timedelta(minutes=intelligence_minutes)

        if now >= next_gov:
            run("run_governance.py")
            next_gov = now + timedelta(minutes=governance_minutes)

        time.sleep(10)
