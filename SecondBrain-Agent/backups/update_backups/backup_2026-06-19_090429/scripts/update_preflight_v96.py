from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from secondbrain.production_ready_v96 import create_update_backup, write_installer_report, write_settings_report, write_production_ready_gate

if __name__ == "__main__":
    print("Update Preflight v9.6")
    print("Backup:", create_update_backup())
    print("Installer:", write_installer_report())
    print("Settings:", write_settings_report())
    print("Gate:", write_production_ready_gate())
