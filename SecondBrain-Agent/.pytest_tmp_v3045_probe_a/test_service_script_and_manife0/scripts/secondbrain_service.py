# pywin32 Windows Service scaffold for SecondBrainOS
# Install:
#   pip install pywin32
#   python scripts\secondbrain_service.py install
#   python scripts\secondbrain_service.py start

import subprocess
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    subprocess.call(["python", "launcher.py", "svc-run"], cwd=str(root))
