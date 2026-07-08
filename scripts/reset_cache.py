from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.reset import reset_cache

if __name__ == "__main__":
    changed = reset_cache(PROJECT_ROOT)
    print("Cache zurückgesetzt:")
    for item in changed:
        print("-", item)
