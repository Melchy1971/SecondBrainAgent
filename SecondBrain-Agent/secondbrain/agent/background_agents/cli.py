"""v30.63 Background Agents - launcher CLI.

Commands wired into launcher.py:
    background-agent-list
    background-agent-register --name TEXT --type TYPE [--interval SECONDS]
                             [--max-failures N] [--on-failure pause|stop|alert_only]
    background-agent-start   <agent_id>
    background-agent-stop    <agent_id>
    background-agent-pause   <agent_id>
    background-agent-status  <agent_id>
    background-agent-run     <agent_id> [--force]
    background-agent-run-due
    background-agent-runs    [<agent_id>] [--limit N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import BackgroundAgentService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="background-agent")
    parser.add_argument("cmd")
    parser.add_argument("agent_id", nargs="?")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--type", dest="agent_type", default=None)
    parser.add_argument("--interval", type=int, default=0)
    parser.add_argument("--max-failures", type=int, default=3)
    parser.add_argument("--on-failure", default="pause")
    parser.add_argument("--config-json", default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    service = BackgroundAgentService(root or args.project_root)
    cmd = args.cmd

    if cmd == "background-agent-list":
        _out(service.list())
        return 0

    if cmd == "background-agent-register":
        if not args.name or not args.agent_type:
            _out({"ok": False, "error": "name_and_type_required",
                  "agent_types": service.agent_types()})
            return 2
        config = json.loads(args.config_json) if args.config_json else {}
        try:
            _out(service.register(args.name, args.agent_type, interval_seconds=args.interval,
                                  max_consecutive_failures=args.max_failures,
                                  action=args.on_failure, config=config))
        except ValueError as exc:
            _out({"ok": False, "error": f"invalid_agent_type:{exc}",
                  "agent_types": service.agent_types()})
            return 2
        return 0

    if cmd == "background-agent-run-due":
        _out(service.run_due())
        return 0

    if cmd == "background-agent-runs":
        _out(service.runs(args.agent_id, limit=args.limit))
        return 0

    if cmd in {"background-agent-start", "background-agent-stop", "background-agent-pause",
               "background-agent-status", "background-agent-run"}:
        if not args.agent_id:
            _out({"ok": False, "error": "agent_id_required"})
            return 2
        try:
            if cmd == "background-agent-start":
                payload = service.start(args.agent_id)
            elif cmd == "background-agent-stop":
                payload = service.stop(args.agent_id)
            elif cmd == "background-agent-pause":
                payload = service.pause(args.agent_id)
            elif cmd == "background-agent-run":
                payload = service.run(args.agent_id, force=args.force)
            else:
                payload = service.status(args.agent_id)
        except KeyError as exc:
            _out({"ok": False, "error": str(exc)})
            return 2
        _out(payload)
        return 0

    _out({"ok": False, "error": f"unknown_command:{cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
