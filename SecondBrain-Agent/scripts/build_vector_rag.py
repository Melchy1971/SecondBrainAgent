from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.vector_rag_v95 import build_vector_index
if __name__ == "__main__":
    print(build_vector_index())
