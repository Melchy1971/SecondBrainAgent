from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.production_ready_v96 import write_settings_report
if __name__ == "__main__":
    print(write_settings_report())
