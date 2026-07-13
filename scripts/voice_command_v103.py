from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.voice_layer_v103 import route_voice_command
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\voice_command_v103.py \"Befehl\" [--execute]")
        raise SystemExit(1)
    execute = "--execute" in sys.argv
    command = " ".join(a for a in sys.argv[1:] if a != "--execute")
    print(route_voice_command(command, execute=execute))
