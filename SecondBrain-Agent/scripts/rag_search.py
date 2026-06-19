from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.vector_rag_v95 import write_rag_result
if __name__ == "__main__":
    q = " ".join(sys.argv[1:]).strip() or input("RAG Suche: ").strip()
    print(write_rag_result(q))
