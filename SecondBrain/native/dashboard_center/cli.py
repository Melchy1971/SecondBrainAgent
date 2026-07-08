from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import NativeDashboardService


def _out(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain dashboard-center")
    parser.add_argument("cmd", choices=[
        "dashboard-center",
        "dashboard-center-gui",
        "dashboard-center-status",
        "dashboard-center-snapshot",
        "dashboard-center-activity",
        "dashboard-center-record",
    ])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--limit", type=int, default=50)
    ns, _ = parser.parse_known_args(argv)
    service = NativeDashboardService(ns.project_root)

    if ns.cmd in {"dashboard-center", "dashboard-center-gui"}:
        from .gui import run_gui

        run_gui(ns.project_root)
        return 0
    if ns.cmd == "dashboard-center-status":
        payload = service.status()
    elif ns.cmd == "dashboard-center-snapshot":
        payload = service.snapshot().to_dict()
    elif ns.cmd == "dashboard-center-activity":
        payload = service.activity(limit=ns.limit)
    elif ns.cmd == "dashboard-center-record":
        event = ns.args[0] if ns.args else "manual_dashboard_event"
        payload = service.record_activity(event, {"args": ns.args[1:]})
    else:
        payload = {"ok": False, "error": "unknown_command", "cmd": ns.cmd}
    _out(payload)
    return 0 if payload.get("ok") else 1
