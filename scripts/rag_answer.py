from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.ollama_rag_v95 import answer_with_rag
if __name__ == "__main__":
    q = " ".join(sys.argv[1:]).strip() or input("Frage: ").strip()
    print(answer_with_rag(q))
