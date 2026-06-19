from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.voice_layer_v103 import import_dictation_file, import_dictation_folder
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        print(import_dictation_file(sys.argv[1]))
    else:
        for o in import_dictation_folder():
            print(o)
