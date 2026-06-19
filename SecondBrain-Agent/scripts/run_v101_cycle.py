from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.connector_foundation_v101 import write_connector_status
from secondbrain.document_ingestion_v101 import write_ingestion_status
from secondbrain.dashboard_api_v101 import write_dashboard_catalog

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v10_cycle.py")
    outputs = [
        write_connector_status(),
        write_ingestion_status(),
        write_dashboard_catalog(),
    ]
    print("SecondBrain v10.1 MCP & Connector Foundation Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
