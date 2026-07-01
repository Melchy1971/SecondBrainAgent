from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import ThemeCenterService


def _out(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain theme-center")
    parser.add_argument("cmd")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--output", default=None)
    parser.add_argument("--limit", type=int, default=30)
    ns, _ = parser.parse_known_args(argv)
    svc = ThemeCenterService(ns.project_root)
    cmd = ns.cmd

    if cmd in {"theme-center", "theme-status"}:
        payload = svc.status()
    elif cmd == "theme-list":
        payload = svc.list_themes()
    elif cmd == "theme-current":
        payload = {"ok": True, "theme": svc.current_theme().to_dict()}
    elif cmd == "theme-activate":
        payload = svc.activate(ns.args[0] if ns.args else "")
    elif cmd == "theme-preview":
        payload = svc.preview(ns.args[0] if ns.args else svc.current_theme_id())
    elif cmd == "theme-export":
        payload = svc.export_theme(ns.args[0] if ns.args else svc.current_theme_id(), ns.output)
    elif cmd == "theme-import":
        payload = svc.import_theme(ns.args[0] if ns.args else "")
    elif cmd == "theme-reset":
        payload = svc.reset()
    elif cmd == "theme-history":
        payload = svc.history(ns.limit)
    elif cmd == "theme-center-gui":
        from .gui import run_gui
        payload = run_gui(ns.project_root)
    else:
        payload = {"ok": False, "error": "unknown_command", "cmd": cmd}

    _out(payload)
    return 0 if payload.get("ok") else 1
