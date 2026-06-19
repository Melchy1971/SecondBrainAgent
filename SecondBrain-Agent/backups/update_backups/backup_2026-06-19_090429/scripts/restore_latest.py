from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.restore import restore_latest_config_cache

if __name__ == "__main__":
    restored = restore_latest_config_cache(PROJECT_ROOT)
    if restored:
        print(f"Wiederhergestellt aus: {restored}")
    else:
        print("Kein Backup gefunden.")
