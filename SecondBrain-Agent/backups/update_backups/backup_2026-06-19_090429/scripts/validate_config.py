from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.validator import validate_environment

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    result = validate_environment(settings, PROJECT_ROOT)

    print("Konfigurationsvalidierung")
    print("Status:", "OK" if result["ok"] else "BLOCKIERT")
    print("")

    for name, ok, hint in result["checks"]:
        status = "OK" if ok else "FEHLT"
        print(f"{status:6} {name} — {hint}")
