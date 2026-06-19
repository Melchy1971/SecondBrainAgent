from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    semantic = PROJECT_ROOT / "scripts" / "semantic_search.py"
    os_cycle = PROJECT_ROOT / "scripts" / "run_secondbrain_os_cycle.py"

    if semantic.exists():
        subprocess.run([sys.executable, str(semantic), "ChatGPT"], cwd=str(PROJECT_ROOT))

    if os_cycle.exists():
        subprocess.run([sys.executable, str(os_cycle)], cwd=str(PROJECT_ROOT))

    print("ChatGPT Index Update abgeschlossen.")
