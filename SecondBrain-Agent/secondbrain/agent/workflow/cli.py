"""v30.62 Agent Workflow Engine - launcher CLI.

Commands wired into launcher.py:
    workflow-create  --objective TEXT (--steps-json JSON | --spec PATH)
    workflow-run     <workflow_id>
    workflow-status  <workflow_id>
    workflow-list
    workflow-cancel  <workflow_id>
    workflow-resume  <workflow_id>
    workflow-audit   [<workflow_id>] [--limit N]
    workflow-rollback <workflow_id>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import WorkflowService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="workflow")
    parser.add_argument("cmd")
    parser.add_argument("workflow_id", nargs="?")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--objective", default="")
    parser.add_argument("--steps-json", default=None)
    parser.add_argument("--spec", default=None)
    parser.add_argument("--limit", type=int, default=200)
    return parser


def _load_steps(args) -> list[dict]:
    if args.steps_json:
        return json.loads(args.steps_json)
    if args.spec:
        data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return list(data.get("steps", []))
        return list(data)
    return []


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    project_root = root or args.project_root
    service = WorkflowService(project_root)
    cmd = args.cmd

    if cmd == "workflow-create":
        steps = _load_steps(args)
        if not args.objective and not steps:
            _out({"ok": False, "error": "objective_or_steps_required"})
            return 2
        _out(service.create(args.objective, steps))
        return 0

    if cmd in {"workflow-run", "workflow-status", "workflow-cancel", "workflow-resume", "workflow-rollback"}:
        if not args.workflow_id:
            _out({"ok": False, "error": "workflow_id_required"})
            return 2
        try:
            if cmd == "workflow-run":
                payload = service.run(args.workflow_id)
            elif cmd == "workflow-status":
                payload = service.status(args.workflow_id)
            elif cmd == "workflow-cancel":
                payload = service.cancel(args.workflow_id)
            elif cmd == "workflow-rollback":
                payload = service.prepare_rollback(args.workflow_id)
            else:
                payload = service.resume(args.workflow_id)
        except KeyError as exc:
            _out({"ok": False, "error": str(exc)})
            return 2
        _out(payload)
        return 0

    if cmd == "workflow-list":
        _out(service.list())
        return 0

    if cmd == "workflow-audit":
        _out(service.audit(args.workflow_id, limit=args.limit))
        return 0

    _out({"ok": False, "error": f"unknown_command:{cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
