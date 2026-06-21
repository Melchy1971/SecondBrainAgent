from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.jarvis_hud_server import start

if __name__ == "__main__":
    start()
