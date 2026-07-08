from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.simulation_engine import run_simulation

if __name__ == "__main__":
    scenario = " ".join(sys.argv[1:]).strip()
    if not scenario:
        scenario = input("Szenario: ").strip()
    settings = load_settings(PROJECT_ROOT)
    target = run_simulation(settings, scenario)
    print(f"Simulation erstellt: {target}")
