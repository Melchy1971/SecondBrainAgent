from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.gui.launch import gui_command

if __name__ == "__main__":
    raise SystemExit(gui_command(["jarvis", "--project-root", str(ROOT)] + sys.argv[1:]))
