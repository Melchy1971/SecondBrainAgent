from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.memory_engine_v97 import build_memory_profile
from secondbrain.self_reflection_v97 import write_self_reflection
from secondbrain.reasoning_engine_v97 import write_reasoning_map
from secondbrain.goal_system_v97 import write_goal_map
from secondbrain.daily_assistant_v97 import write_daily_assistant
from secondbrain.weekly_review_v97 import write_weekly_review

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v95_cycle.py")
    outputs = [
        build_memory_profile(),
        write_self_reflection(),
        write_reasoning_map(),
        write_goal_map(),
        write_daily_assistant(),
        write_weekly_review(),
    ]
    print("SecondBrain v9.7 AI Copilot Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
