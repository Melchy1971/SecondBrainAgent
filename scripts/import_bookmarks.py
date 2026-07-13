from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.connectors_real import import_browser_bookmarks

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Nutzung: python scripts\\import_bookmarks.py <Chrome|Edge|Firefox> <Bookmarks-Datei>")
        raise SystemExit(1)
    settings = load_settings(PROJECT_ROOT)
    target = import_browser_bookmarks(settings, sys.argv[2], sys.argv[1])
    print(f"Bookmarks importiert: {target}")
