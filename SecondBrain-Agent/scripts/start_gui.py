"""Kompatibilitaets-Starter: leitet auf das Jarvis HUD um (eine GUI).

Frueher startete dieses Skript die alte Control-Center-GUI
(gui_backend_v102, Port 8850). Seit der Konsolidierung auf eine einzige
Oberflaeche startet es das HUD (start_hud.py, Port 8851). Die Datei
gui_backend_v102.py bleibt nur noch als Bibliothek erhalten (die HUD
verwendet deren Funktionen weiter) und wird nicht mehr als GUI gestartet.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    runpy.run_path(str(ROOT / "scripts" / "start_hud.py"), run_name="__main__")
