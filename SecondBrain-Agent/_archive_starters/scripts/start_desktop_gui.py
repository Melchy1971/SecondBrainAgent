"""Headless-Starter fuer die Desktop-GUI mit Live-Daten.

Baut die GUI-App mit realer Datenbindung, fuehrt die Startup-Checks aus und
rendert das Shell-Modell sowie die Live-View-Models aller Module als JSON.
Dient als verifizierbarer Live-Lauf (kein GUI-Toolkit erforderlich).

Aufruf:
    python scripts/start_desktop_gui.py            # Uebersicht
    python scripts/start_desktop_gui.py --json     # vollstaendig als JSON
    python scripts/start_desktop_gui.py <module>   # ein Modul live
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secondbrain.desktop.gui.gui_app import GuiApp  # noqa: E402


def build() -> GuiApp:
    app = GuiApp.create_live(ROOT)
    app.start()
    return app


def collect(app: GuiApp) -> dict:
    shell = app.render_shell()
    modules = [item["id"] for item in shell.sidebar]
    return {
        "startup_status": app.state.startup_status,
        "recovery_mode": app.state.recovery_mode,
        "health": app.state.health_snapshot,
        "modules": modules,
        "views": {mid: app.render_module_live(mid) for mid in modules},
    }


def main(argv: list[str]) -> int:
    app = build()
    data = collect(app)

    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    single = next((a for a in argv if not a.startswith("-")), None)
    if single:
        print(json.dumps(app.render_module_live(single), ensure_ascii=False, indent=2))
        return 0

    print(f"Startup: {data['startup_status']}  (recovery={data['recovery_mode']})")
    print("Checks: " + ", ".join(f"{k}={v}" for k, v in data["health"].items()))
    print()
    for mid in data["modules"]:
        view = data["views"][mid]
        summary = {k: (f"{len(v)} Eintraege" if isinstance(v, list) else v)
                   for k, v in view.items() if k not in ("items", "hits")}
        print(f"[{mid}]")
        for k, v in summary.items():
            print(f"   {k}: {v}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
