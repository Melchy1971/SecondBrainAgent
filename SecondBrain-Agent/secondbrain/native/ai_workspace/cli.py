from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import AIWorkspaceService


def _out(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain ai-workspace")
    parser.add_argument("cmd", choices=[
        "ai-workspace", "ai-workspace-gui", "ai-workspace-status",
        "ai-workspace-snapshot", "ai-workspace-navigation",
        "ai-workspace-activity", "ai-workspace-record",
    ])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--limit", type=int, default=30)
    ns, _ = parser.parse_known_args(argv)
    service = AIWorkspaceService(ns.project_root)

    if ns.cmd in {"ai-workspace", "ai-workspace-gui"}:
        from .gui import run_gui
        return run_gui(ns.project_root)
    if ns.cmd == "ai-workspace-status":
        payload = service.status()
    elif ns.cmd == "ai-workspace-snapshot":
        payload = service.snapshot().to_dict()
    elif ns.cmd == "ai-workspace-navigation":
        payload = service.navigation()
    elif ns.cmd == "ai-workspace-activity":
        payload = service.activity(limit=max(0, ns.limit))
    elif ns.cmd == "ai-workspace-record":
        event = ns.args[0] if ns.args else "manual_workspace_event"
        payload = service.record_activity(event, {"args": ns.args[1:]})
    else:  # pragma: no cover
        payload = {"ok": False, "error": "unknown_command", "cmd": ns.cmd}
    _out(payload)
    return 0 if payload.get("ok") else 1
