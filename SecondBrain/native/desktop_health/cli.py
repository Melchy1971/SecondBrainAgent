from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import NativeDesktopHealthService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain native-desktop-health")
    parser.add_argument("cmd", choices=["native-desktop-health", "native-desktop-doctor", "native-desktop-report"])
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--target", default=None)
    args, _ = parser.parse_known_args(argv)
    service = NativeDesktopHealthService(args.project_root)
    payload = service.write_report(args.target) if args.cmd == "native-desktop-report" else service.status()
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return 0 if payload.get("ok") else 1
