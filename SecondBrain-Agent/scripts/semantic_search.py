from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.semantic_search_engine import write_search_result

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Suchfrage: ").strip()
    settings = load_settings(PROJECT_ROOT)
    target = write_search_result(settings, query)
    print(f"Semantic Search Ergebnis: {target}")
