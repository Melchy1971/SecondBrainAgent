"""v30.65 Agent Goal Tracking - launcher CLI.

Commands wired into launcher.py:
    goal-create  --title TEXT [--description TEXT] [--target-date ISO] [--owner NAME]
                 [--metric name:target[:current[:direction]]]... [--milestone TITLE]... [--decompose]
    goal-list
    goal-show    <goal_id>
    goal-update  <goal_id> [--metric name=value] [--complete-milestone ID]
                 [--add-milestone TITLE] [--status pause|resume|cancel] [--decompose] [--evidence NOTE]
    goal-report  <goal_id>
    goal-close   <goal_id> [--force]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import GoalService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="goal")
    parser.add_argument("cmd")
    parser.add_argument("goal_id", nargs="?")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--description", default="")
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--owner", default="")
    parser.add_argument("--metric", action="append", default=[])
    parser.add_argument("--milestone", action="append", default=[])
    parser.add_argument("--complete-milestone", default=None)
    parser.add_argument("--add-milestone", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--decompose", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def _parse_metric_spec(spec: str) -> dict:
    # name:target[:current[:direction]]
    parts = spec.split(":")
    return {
        "name": parts[0],
        "target": float(parts[1]) if len(parts) > 1 and parts[1] else 0.0,
        "current": float(parts[2]) if len(parts) > 2 and parts[2] else 0.0,
        "direction": parts[3] if len(parts) > 3 and parts[3] else "increase",
    }


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    service = GoalService(root or args.project_root)
    cmd = args.cmd

    if cmd == "goal-create":
        if not args.title:
            _out({"ok": False, "error": "title_required"})
            return 2
        metrics = [_parse_metric_spec(s) for s in args.metric]
        milestones = [{"title": t} for t in args.milestone]
        _out(service.create(args.title, description=args.description, target_date=args.target_date,
                            owner=args.owner, metrics=metrics, milestones=milestones,
                            decompose=args.decompose))
        return 0

    if cmd == "goal-list":
        _out(service.list())
        return 0

    if cmd in {"goal-show", "goal-report", "goal-close", "goal-update"}:
        if not args.goal_id:
            _out({"ok": False, "error": "goal_id_required"})
            return 2
        try:
            if cmd == "goal-show":
                payload = service.show(args.goal_id)
            elif cmd == "goal-report":
                payload = service.report(args.goal_id)
            elif cmd == "goal-close":
                payload = service.close(args.goal_id, force=args.force)
            else:
                payload = service.update(
                    args.goal_id, metric=args.metric[0] if args.metric else None,
                    complete_milestone=args.complete_milestone, add_milestone=args.add_milestone,
                    status=args.status, decompose=args.decompose, evidence=args.evidence)
        except (KeyError, ValueError, RuntimeError) as exc:
            _out({"ok": False, "error": str(exc)})
            return 2
        _out(payload)
        return 0

    _out({"ok": False, "error": f"unknown_command:{cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
