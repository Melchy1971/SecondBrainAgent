from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.persistent_agent_memory import write_agent_memories
from secondbrain.agent_collaboration import write_collaboration_protocol
from secondbrain.goal_engine import write_goal_map
from secondbrain.autonomous_planner import write_plans
from secondbrain.personal_kpi_engine import write_kpi_dashboard
from secondbrain.decision_journal import write_decision_journal
from secondbrain.enterprise_rag import write_enterprise_rag_status
from secondbrain.twins import write_twin_reports
from secondbrain.data_warehouse import write_data_warehouse
from secondbrain.semantic_os import write_semantic_os_status
from secondbrain.local_ai_cluster import write_local_ai_cluster
from secondbrain.software_factory import write_software_factory
from secondbrain.business_os import write_business_os
from secondbrain.personal_agi_os import write_personal_agi_os

def run(script):
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    run("run_life_os_cycle.py")
    outputs = []
    outputs.extend(write_agent_memories(settings))
    outputs.append(write_collaboration_protocol(settings))
    outputs.append(write_goal_map(PROJECT_ROOT, settings))
    outputs.extend(write_plans(settings))
    outputs.append(write_kpi_dashboard(settings))
    outputs.append(write_decision_journal(settings))
    outputs.append(write_enterprise_rag_status(settings))
    outputs.extend(write_twin_reports(settings))
    outputs.extend(write_data_warehouse(settings))
    outputs.append(write_semantic_os_status(settings))
    outputs.append(write_local_ai_cluster(settings))
    outputs.append(write_software_factory(settings))
    outputs.append(write_business_os(settings))
    outputs.append(write_personal_agi_os(settings))
    print("AGI OS Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
