from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import NativeLayoutService


def _out(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain layout-center")
    parser.add_argument("cmd", choices=[
        "layout-center",
        "layout-center-gui",
        "layout-status",
        "layout-list",
        "layout-load",
        "layout-activate",
        "layout-save",
        "layout-reset",
        "layout-export",
        "layout-import",
        "layout-history",
    ])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--target", default=None)
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    ns, _ = parser.parse_known_args(argv)
    service = NativeLayoutService(ns.project_root)

    if ns.cmd in {"layout-center", "layout-center-gui"}:
        from .gui import run_gui

        run_gui(ns.project_root)
        return 0
    if ns.cmd == "layout-status":
        payload = service.status()
    elif ns.cmd == "layout-list":
        payload = service.list_layouts()
    elif ns.cmd == "layout-load":
        payload = service.load(ns.args[0] if ns.args else None)
    elif ns.cmd == "layout-activate":
        payload = service.activate(ns.args[0] if ns.args else service.DEFAULT_LAYOUT)
    elif ns.cmd == "layout-save":
        payload = {"ok": False, "error": "layout_save_requires_json_contract", "hint": "Use layout-import for external JSON layouts."}
    elif ns.cmd == "layout-reset":
        payload = service.reset(ns.args[0] if ns.args else None)
    elif ns.cmd == "layout-export":
        payload = service.export(ns.args[0] if ns.args else service.active_name(), target=ns.target)
    elif ns.cmd == "layout-import":
        if not ns.args:
            payload = {"ok": False, "error": "missing_source"}
        else:
            payload = service.import_layout(ns.args[0], activate=ns.activate)
    elif ns.cmd == "layout-history":
        payload = service.history(limit=ns.limit)
    else:
        payload = {"ok": False, "error": "unknown_command", "cmd": ns.cmd}
    _out(payload)
    return 0 if payload.get("ok") else 1
