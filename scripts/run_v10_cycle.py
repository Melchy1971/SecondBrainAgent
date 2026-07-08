from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.life_dashboard_v10 import write_life_dashboard
from secondbrain.daily_os_v10 import write_daily_os
from secondbrain.weekly_os_v10 import write_weekly_os
from secondbrain.personal_kpis_v10 import write_personal_kpis
from secondbrain.personal_erp_v10 import write_personal_erp
from secondbrain.jarvis_copilot_v10 import write_jarvis_copilot
from secondbrain.command_center_v10 import write_command_center

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v99_cycle.py")
    outputs = [
        write_life_dashboard(),
        write_daily_os(),
        write_weekly_os(),
        write_personal_kpis(),
        *write_personal_erp(),
        write_jarvis_copilot(),
        write_command_center(),
    ]
    print("SecondBrain v10 Personal OS Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
