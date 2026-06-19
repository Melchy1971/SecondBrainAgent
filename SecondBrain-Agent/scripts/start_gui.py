from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.gui_backend_v102 import start

if __name__ == "__main__":
    start()
