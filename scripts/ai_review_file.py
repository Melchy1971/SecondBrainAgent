from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.ai_review_queue import review_one_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts\\ai_review_file.py <Markdown-Datei>")
        raise SystemExit(1)
    settings = load_settings(PROJECT_ROOT)
    target = review_one_file(PROJECT_ROOT, settings, sys.argv[1])
    print(f"AI Review erstellt: {target}")
