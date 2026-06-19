from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.connectors_real import index_code_repository

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\index_code_repo.py <Repo-Pfad>")
        raise SystemExit(1)
    settings = load_settings(PROJECT_ROOT)
    target = index_code_repository(settings, sys.argv[1])
    print(f"Code Index erstellt: {target}")
