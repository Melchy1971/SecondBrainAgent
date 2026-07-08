"""v30.66 Native Agent Control - launcher CLI.

Commands wired into launcher.py:
    agent-control-center            -> overview (JSON)
    agent-control-center-gui        -> launch embedded panel as standalone window
    agent-control-center-status     -> overview
    agent-control-area <area>       -> one area (agents|plans|workflows|
                                       background_agents|approvals|goals|audit|logs)
    agent-control-plan-create --goal TEXT
    agent-control-plan-inspect <plan_id>
    agent-control-plan-start <plan_id>
    agent-control-approve <approval_id> [--by NAME]
    agent-control-reject  <approval_id> [--by NAME]
    agent-control-workflow <workflow_id>
    agent-control-goal-report <goal_id>
    agent-control-bg <agent_id> --action start|stop|pause|resume|run
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import AgentControlService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-control-center")
    parser.add_argument("cmd")
    parser.add_argument("target", nargs="?")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--goal", default=None)
    parser.add_argument("--by", default="user")
    parser.add_argument("--action", default=None)
    return parser


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    project_root = root or args.project_root
    service = AgentControlService(project_root)
    cmd = args.cmd

    if cmd == "agent-control-center-gui":
        from .gui import run_gui
        return run_gui(project_root)

    if cmd in {"agent-control-center", "agent-control-center-status"}:
        _out(service.overview())
        return 0

    if cmd == "agent-control-area":
        if not args.target:
            _out({"ok": False, "error": "area_required"})
            return 2
        _out(service.area(args.target))
        return 0

    if cmd == "agent-control-plan-create":
        if not args.goal:
            _out({"ok": False, "error": "goal_required"})
            return 2
        _out(service.create_plan(args.goal))
        return 0

    try:
        if cmd == "agent-control-plan-inspect":
            payload = service.inspect_plan(args.target)
        elif cmd == "agent-control-plan-start":
            payload = service.start_plan(args.target)
        elif cmd == "agent-control-approve":
            payload = service.approve(args.target, decided_by=args.by)
        elif cmd == "agent-control-reject":
            payload = service.reject(args.target, decided_by=args.by)
        elif cmd == "agent-control-workflow":
            payload = service.monitor_workflow(args.target)
        elif cmd == "agent-control-goal-report":
            payload = service.goal_report(args.target)
        elif cmd == "agent-control-bg":
            payload = service.manage_background_agent(args.target, args.action or "")
        else:
            _out({"ok": False, "error": f"unknown_command:{cmd}"})
            return 2
    except (KeyError, ValueError, RuntimeError) as exc:
        _out({"ok": False, "error": str(exc)})
        return 2
    if not args.target:
        _out({"ok": False, "error": "target_required"})
        return 2
    _out(payload)
    return 0 if payload.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
