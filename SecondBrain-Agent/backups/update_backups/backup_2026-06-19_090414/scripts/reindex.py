from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from secondbrain.config import load_settings
from secondbrain.reindex import build_vault_index

if __name__ == "__main__":
    settings = load_settings(PROJECT_ROOT)
    target = build_vault_index(settings)
    print(f"Vault-Index erstellt: {target}")
