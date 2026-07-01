from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import NotificationCenterService


def _out(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="notification-center")
    parser.add_argument("cmd")
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--level", default="info")
    parser.add_argument("--category", default="system")
    parser.add_argument("--source", default="native")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--unread", action="store_true")
    parser.add_argument("--action-required", action="store_true")
    parser.add_argument("--keep-unread", action="store_true")
    args = parser.parse_args(argv)
    svc = NotificationCenterService(args.project_root)

    if args.cmd in {"notification-center", "notification-center-status"}:
        payload = svc.status()
    elif args.cmd == "notification-list":
        payload = svc.list_items(limit=args.limit, unread_only=args.unread, category=args.category if args.category != "system" else None)
    elif args.cmd == "notification-send":
        title = args.args[0] if args.args else "Benachrichtigung"
        message = " ".join(args.args[1:]) if len(args.args) > 1 else title
        payload = svc.notify(title=title, message=message, level=args.level, category=args.category, source=args.source, action_required=args.action_required)
    elif args.cmd == "notification-read":
        payload = svc.mark_read(args.args[0] if args.args else "")
    elif args.cmd == "notification-read-all":
        payload = svc.mark_all_read()
    elif args.cmd == "notification-clear":
        payload = svc.clear(keep_unread=args.keep_unread)
    elif args.cmd == "notification-center-gui":
        from .gui import run
        run(args.project_root)
        return 0
    else:
        payload = {"ok": False, "error": "unknown_command", "cmd": args.cmd}

    _out(payload)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
