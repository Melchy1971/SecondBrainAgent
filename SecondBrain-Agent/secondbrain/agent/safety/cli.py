"""v30.61 Agent Safety Layer - launcher CLI.

Commands wired into launcher.py:
    approval-list     [--status pending|approved|rejected|expired] [--json]
    approval-show     <approval_id>
    approval-approve  <approval_id> [--by NAME]
    approval-reject   <approval_id> [--by NAME]
    approval-audit    [--limit N] [--all]

Also exposes the expiry sweep for scheduled runs:
    approval-expire   [--ttl SECONDS] [--by NAME]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .guard import DEFAULT_TTL_SECONDS, SafetyService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="approval")
    parser.add_argument("cmd")
    parser.add_argument("approval_id", nargs="?")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--by", default="user")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)
    parser.add_argument("--all", action="store_true", help="include non-safety audit events")
    return parser


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    project_root = root or args.project_root
    service = SafetyService(project_root)
    cmd = args.cmd

    if cmd == "approval-list":
        rows = service.list(status=args.status)
        _out({"ok": True, "count": len(rows), "status": args.status or "all", "approvals": rows})
        return 0

    if cmd == "approval-show":
        if not args.approval_id:
            _out({"ok": False, "error": "approval_id_required"})
            return 2
        record = service.get(args.approval_id)
        if record is None:
            _out({"ok": False, "error": "approval_not_found", "approval_id": args.approval_id})
            return 2
        _out({"ok": True, "approval": record})
        return 0

    if cmd == "approval-approve":
        if not args.approval_id:
            _out({"ok": False, "error": "approval_id_required"})
            return 2
        decision = service.approve(args.approval_id, decided_by=args.by)
        _out(decision.to_dict())
        return 0 if decision.ok else 2

    if cmd == "approval-reject":
        if not args.approval_id:
            _out({"ok": False, "error": "approval_id_required"})
            return 2
        decision = service.reject(args.approval_id, decided_by=args.by)
        _out(decision.to_dict())
        return 0 if decision.ok else 2

    if cmd == "approval-expire":
        decisions = service.expire(ttl_seconds=args.ttl, decided_by=args.by or "system")
        _out({"ok": True, "expired": len(decisions), "decisions": [d.to_dict() for d in decisions]})
        return 0

    if cmd == "approval-audit":
        events = service.audit_events(limit=args.limit, safety_only=not args.all)
        _out({"ok": True, "count": len(events), "events": events})
        return 0

    _out({"ok": False, "error": f"unknown_command:{cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
