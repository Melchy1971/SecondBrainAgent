from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.context_engine import build_context_map
from secondbrain.memory_engine import build_memory_profile
from secondbrain.temporal_graph import build_temporal_graph
from secondbrain.lineage_engine import build_lineage_index
from secondbrain.self_healing import detect_healing_actions
from secondbrain.compression_engine import compress_knowledge
from secondbrain.semantic_deduplication import write_semantic_dedup_report
from secondbrain.research_agent import write_research_backlog
from secondbrain.decision_intelligence import write_decision_intelligence
from secondbrain.predictive_engine import write_prediction_report
from secondbrain.simulation_engine import run_simulation
from secondbrain.process_mining import write_process_mining_report
from secondbrain.process_copilot import write_process_copilot_templates
from secondbrain.executive_dashboard import write_executive_dashboard
from secondbrain.personal_erp import write_personal_erp_indexes
from secondbrain.agent_swarm import write_agent_swarm_status
from secondbrain.chief_of_staff_v2 import write_chief_of_staff_v2

def run(script):
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    run("run_autonomy_cycle.py")
    outputs = []
    outputs.append(build_context_map(settings))
    outputs.append(build_memory_profile(settings))
    outputs.append(build_temporal_graph(settings))
    outputs.append(build_lineage_index(settings))
    outputs.append(detect_healing_actions(settings))
    outputs.append(compress_knowledge(settings))
    outputs.append(write_semantic_dedup_report(settings))
    outputs.append(write_research_backlog(settings))
    outputs.append(write_decision_intelligence(settings))
    outputs.append(write_prediction_report(settings))
    outputs.append(run_simulation(settings, "Was passiert wenn ein zentrales Projekt blockiert ist"))
    outputs.append(write_process_mining_report(settings))
    outputs.append(write_process_copilot_templates(settings))
    outputs.append(write_executive_dashboard(settings))
    outputs.extend(write_personal_erp_indexes(settings))
    outputs.append(write_agent_swarm_status(settings))
    outputs.append(write_chief_of_staff_v2(settings))

    print("OS Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
