from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.weighted_graph import update_weighted_graph

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    target = update_weighted_graph(settings)
    print(f"Weighted Graph aktualisiert: {target}")
