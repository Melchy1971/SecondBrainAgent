from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.personal_search import personal_search

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = input("Suche: ").strip()
    settings = load_settings(PROJECT_ROOT)
    target = personal_search(settings, query)
    print(f"Suchergebnis erstellt: {target}")
