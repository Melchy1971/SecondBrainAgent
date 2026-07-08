"""Launcher helper: build a provider CLI (login/sync/status/disconnect)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable


def run_connector_cli(prefix: str, runtime_factory: Callable, argv: list[str], *, out: Callable, config_error) -> int:
    """prefix e.g. 'm365' or 'google'. runtime_factory(project_root) -> runtime facade."""
    parser = argparse.ArgumentParser(prog="secondbrain")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--resources", default=None)
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--approve", default=None)
    args, _ = parser.parse_known_args(argv)

    try:
        runtime = runtime_factory(args.project_root)
    except config_error as exc:
        out({"status": "config_error", "message": str(exc)})
        return 2

    resources = [r.strip() for r in args.resources.split(",") if r.strip()] if args.resources else None
    cmd = args.cmd
    if cmd == f"{prefix}-login":
        result = runtime.login(printer=lambda m: print(m, file=sys.stderr), wait=not args.no_wait)
        out(result)
        return 0 if result.get("status") in {"ok", "pending"} else 1
    if cmd == f"{prefix}-sync":
        out(runtime.sync(resources))
        return 0
    if cmd == f"{prefix}-status":
        if args.approve:
            out(runtime.approve(args.approve))
            return 0
        out(runtime.status())
        return 0
    if cmd == f"{prefix}-disconnect":
        out(runtime.disconnect())
        return 0
    out({"status": "unknown_command", "cmd": cmd})
    return 2
