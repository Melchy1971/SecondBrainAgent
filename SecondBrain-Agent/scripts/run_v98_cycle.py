from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.task_agent_v98 import write_task_agent
from secondbrain.research_agent_v98 import write_research_agent
from secondbrain.meeting_agent_v98 import write_meeting_agent
from secondbrain.project_agent_v98 import write_project_agent
from secondbrain.decision_agent_v98 import write_decision_agent
from secondbrain.process_agent_v98 import write_process_agent
from secondbrain.chief_of_staff_v98 import write_chief_of_staff

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v97_cycle.py")
    outputs = [
        write_task_agent(),
        write_research_agent(),
        write_meeting_agent(),
        write_project_agent(),
        write_decision_agent(),
        write_process_agent(),
        write_chief_of_staff(),
    ]
    print("SecondBrain v9.8 Agentic Work Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
