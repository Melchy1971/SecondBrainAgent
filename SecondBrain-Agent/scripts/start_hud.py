"""Starter fuer das Jarvis HUD. Schreibt eine PID-Datei (fuer Jarvis-stop)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PIDFILE = ROOT / "runtime" / "jarvis_hud.pid"

from secondbrain.jarvis_hud_server import start  # noqa: E402


def main():
    PIDFILE.parent.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(str(os.getpid()), encoding="utf-8")
    try:
        start()
    finally:
        try:
            PIDFILE.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
