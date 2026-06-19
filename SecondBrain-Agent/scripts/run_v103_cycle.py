from pathlib import Path
import sys, subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.voice_layer_v103 import write_voice_status, import_dictation_folder

def try_run(script):
    p = ROOT / "scripts" / script
    if p.exists():
        subprocess.run([sys.executable, str(p)], cwd=str(ROOT))

if __name__ == "__main__":
    try_run("run_v102_cycle.py")
    outputs = [write_voice_status()]
    outputs += [Path(o) for o in import_dictation_folder()]
    print("SecondBrain v10.3 Voice Layer Cycle abgeschlossen:")
    for o in outputs:
        print("-", o)
