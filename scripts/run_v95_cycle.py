from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.vector_rag_v95 import build_vector_index
from secondbrain.meeting_transcription_v95 import write_transcription_status
from secondbrain.connectors_v95 import write_calendar_status, write_email_status
from secondbrain.event_bus_v95 import emit, write_event_summary
from secondbrain.autonomous_agents_v95 import write_agent_status
from secondbrain.v95_control_center import write_v95_control_center

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v9_cycle.py")
    outputs = []
    outputs.append(build_vector_index())
    outputs.append(write_transcription_status())
    outputs.append(write_calendar_status())
    outputs.append(write_email_status())
    emit("v95.cycle_started", {"root": str(ROOT)})
    outputs.append(write_event_summary())
    outputs.append(write_agent_status())
    outputs.append(write_v95_control_center())
    emit("v95.cycle_completed", {"outputs": len(outputs)})
    print("SecondBrain v9.5 Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
