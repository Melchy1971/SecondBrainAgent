from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.semantic_search_engine import build_semantic_index
from secondbrain.full_knowledge_graph import build_full_graph
from secondbrain.agent_memory_v2 import write_agent_memory_v2
from secondbrain.project_intelligence_v8 import write_project_intelligence
from secondbrain.decision_intelligence_v2 import write_decision_intelligence_v2
from secondbrain.meeting_intelligence_v2 import write_meeting_intelligence_v2
from secondbrain.calendar_intelligence import write_calendar_intelligence
from secondbrain.data_warehouse_v2 import write_data_warehouse_v2
from secondbrain.mcp_ecosystem import write_mcp_ecosystem_status
from secondbrain.digital_twin_v5 import write_digital_twin_v5
from secondbrain.self_improving_knowledge import write_self_improvement_plan
from secondbrain.secondbrain_os import write_secondbrain_os_dashboard

def try_run(script):
    p = PROJECT_ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    try_run("run_agi_os_cycle.py")

    outputs = []
    outputs.append(build_semantic_index(settings))
    outputs.append(build_full_graph(settings))
    outputs.extend(write_agent_memory_v2(settings))
    outputs.append(write_project_intelligence(settings))
    outputs.append(write_decision_intelligence_v2(settings))
    outputs.append(write_meeting_intelligence_v2(settings))
    outputs.append(write_calendar_intelligence(settings))
    outputs.extend(write_data_warehouse_v2(settings))
    outputs.append(write_mcp_ecosystem_status(PROJECT_ROOT, settings))
    outputs.append(write_digital_twin_v5(settings))
    outputs.append(write_self_improvement_plan(settings))
    outputs.append(write_secondbrain_os_dashboard(settings))

    print("SecondBrain OS Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
