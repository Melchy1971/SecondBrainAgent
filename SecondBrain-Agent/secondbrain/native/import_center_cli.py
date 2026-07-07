"""Launcher facade for the Import Center embedded in AI Workspace."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from secondbrain.importing import ImportCenterService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain import-center")
    parser.add_argument("cmd", choices=("import-center", "import-status", "import-history"))
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--limit", type=int, default=200)
    args, _ = parser.parse_known_args(argv)
    if args.cmd == "import-center":
        from secondbrain.native.ai_workspace.gui import run_gui
        return run_gui(args.project_root, initial_module="imports")
    center = ImportCenterService(args.project_root)
    payload = center.status() if args.cmd == "import-status" else center.history(limit=max(0, args.limit))
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if payload.get("ok") else 1
