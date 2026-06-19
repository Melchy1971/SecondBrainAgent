from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.autonomy import write_autonomy_report
from secondbrain.governance import write_governance_report

def run(script):
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    run("run_once.py")
    run("run_intelligence_cycle.py")
    gov = write_governance_report(settings)
    auto = write_autonomy_report(settings)
    print("Autonomy Cycle abgeschlossen:")
    print("-", gov)
    print("-", auto)
