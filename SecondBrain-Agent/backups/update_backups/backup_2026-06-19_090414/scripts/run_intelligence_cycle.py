from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.rag import build_rag_index
from secondbrain.project_monitor import write_project_monitor
from secondbrain.knowledge_gaps import write_knowledge_gaps
from secondbrain.decision_engine import write_decision_register
from secondbrain.briefings import write_daily_briefing, write_evening_review
from secondbrain.lifeos import write_lifeos_indexes
from secondbrain.process_intelligence import write_process_map
from secondbrain.learning_system import write_learning_report
from secondbrain.digital_twin import write_digital_twin_profile
from secondbrain.chief_of_staff import write_chief_of_staff_report
from secondbrain.weighted_graph import update_weighted_graph
from secondbrain.recommendations import write_recommendations

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    outputs = []
    outputs.append(build_rag_index(settings))
    outputs.append(write_project_monitor(settings))
    outputs.append(write_knowledge_gaps(settings))
    outputs.append(write_decision_register(settings))
    outputs.append(write_daily_briefing(settings))
    outputs.append(write_evening_review(settings))
    outputs.extend(write_lifeos_indexes(settings))
    outputs.append(write_process_map(settings))
    outputs.append(write_learning_report(settings))
    outputs.append(write_digital_twin_profile(settings))
    outputs.append(write_chief_of_staff_report(settings))
    outputs.append(update_weighted_graph(settings))
    outputs.append(write_recommendations(settings))

    print("Intelligence Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
