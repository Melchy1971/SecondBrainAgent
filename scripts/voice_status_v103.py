from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.voice_layer_v103 import write_voice_status
if __name__ == "__main__":
    print(write_voice_status())
