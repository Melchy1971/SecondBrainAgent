from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.event_bus import emit_event, write_event_summary
from secondbrain.mcp_hub import write_mcp_hub_status
from secondbrain.federation import build_federation_index
from secondbrain.ontology_engine import write_ontology_index
from secondbrain.quality_scoring import write_quality_scores
from secondbrain.refactoring_engine import write_refactoring_proposals
from secondbrain.agent_memory_replay import write_memory_replay
from secondbrain.autonomous_project_manager import write_autonomous_project_plan
from secondbrain.autonomous_process_designer import write_process_design_backlog
from secondbrain.agent_economy import write_agent_economy_report
from secondbrain.plugin_marketplace import write_plugin_marketplace
from secondbrain.life_os import write_life_os_dashboard

def run(script):
    subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=str(PROJECT_ROOT))

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    emit_event(settings, "life_os_cycle_started", {"version": "5.0"})
    run("run_os_cycle.py")

    outputs = []
    outputs.append(write_event_summary(settings))
    outputs.append(write_mcp_hub_status(settings))
    outputs.append(build_federation_index(PROJECT_ROOT, settings))
    outputs.append(write_ontology_index(settings))
    outputs.append(write_quality_scores(settings))
    outputs.append(write_refactoring_proposals(settings))
    outputs.append(write_memory_replay(settings))
    outputs.append(write_autonomous_project_plan(settings))
    outputs.append(write_process_design_backlog(settings))
    outputs.append(write_agent_economy_report(settings))
    outputs.append(write_plugin_marketplace(settings))
    outputs.append(write_life_os_dashboard(settings))

    emit_event(settings, "life_os_cycle_completed", {"outputs": len(outputs)})
    print("Life OS Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
