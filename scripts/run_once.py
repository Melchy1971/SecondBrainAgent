from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.orchestrator.orchestrator import run_once

if __name__ == "__main__":
    imported = run_once(PROJECT_ROOT)
    print(f"Importlauf abgeschlossen. Neue Dateien: {len(imported)}")
