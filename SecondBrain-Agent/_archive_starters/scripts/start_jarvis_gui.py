from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.gui.launch import gui_command  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(gui_command(["gui-open", "--project-root", str(ROOT)] + sys.argv[1:]))
