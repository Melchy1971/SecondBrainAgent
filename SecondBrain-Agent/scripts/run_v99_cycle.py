from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.entity_extraction_v99 import build_entity_index
from secondbrain.relationship_engine_v99 import build_relationships
from secondbrain.temporal_graph_v99 import build_temporal_graph
from secondbrain.contradiction_detection_v99 import write_contradictions
from secondbrain.knowledge_quality_v99 import write_quality_report
from secondbrain.cross_source_intelligence_v99 import write_cross_source_report
from secondbrain.knowledge_dashboard_v99 import write_knowledge_dashboard

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v98_cycle.py")
    outputs = [
        build_entity_index(),
        build_relationships(),
        build_temporal_graph(),
        write_contradictions(),
        write_quality_report(),
        write_cross_source_report(),
        write_knowledge_dashboard(),
    ]
    print("SecondBrain v9.9 Knowledge Intelligence Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
