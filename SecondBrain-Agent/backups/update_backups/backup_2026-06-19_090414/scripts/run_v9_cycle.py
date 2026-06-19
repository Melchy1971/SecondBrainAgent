from pathlib import Path
import sys, subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.workflow_engine_v9 import write_workflow_catalog
from secondbrain.recommendation_engine_v9 import write_recommendations
from secondbrain.learning_engine_v9 import write_learning_plan
from secondbrain.simulation_engine_v9 import simulate
from secondbrain.personal_crm_v9 import write_crm_index
from secondbrain.executive_dashboard_v9 import write_executive_dashboard
from secondbrain.voice_assistant_v9 import write_voice_assistant_status
from secondbrain.monitoring_v9 import write_monitoring_report
from secondbrain.plugin_ecosystem_v9 import write_plugin_ecosystem
from secondbrain.digital_twin_v9 import write_digital_twin_v6
from secondbrain.control_center_v9 import write_control_center

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    # Keep compatible with v8 if available
    try_run("run_secondbrain_os_cycle.py")

    outputs = []
    outputs.append(write_workflow_catalog(VAULT))
    outputs.append(write_recommendations(VAULT))
    outputs.append(write_learning_plan(VAULT))
    outputs.append(simulate(VAULT, "Was passiert wenn ein wichtiges Projekt blockiert ist"))
    outputs.append(write_crm_index(VAULT))
    outputs.append(write_executive_dashboard(VAULT))
    outputs.append(write_voice_assistant_status(VAULT))
    outputs.append(write_monitoring_report(VAULT, ROOT))
    outputs.append(write_plugin_ecosystem(VAULT))
    outputs.append(write_digital_twin_v6(VAULT))
    outputs.append(write_control_center(VAULT))

    print("SecondBrain v9 Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
