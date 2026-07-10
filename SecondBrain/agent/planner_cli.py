from __future__ import annotations

import argparse
import json
from pathlib import Path

from secondbrain.agent.planner import AgentPlanService


COMMANDS = {
    "agent-plan-create",
    "agent-plan-show",
    "agent-plan-explain",
    "agent-plan-list",
    "agent-plan-cancel",
    "agent-plan-resume",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain agent-plan")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("cmd", choices=sorted(COMMANDS))
    parser.add_argument("args", nargs="*")
    parser.add_argument("--workspace-id", default=None)
    options = parser.parse_args(argv)
    service = AgentPlanService(options.project_root)
    try:
        if options.cmd == "agent-plan-create":
            if not options.args:
                raise ValueError("plan_goal_required")
            payload = service.create(" ".join(options.args), workspace_id=options.workspace_id).to_dict()
        elif options.cmd == "agent-plan-list":
            plans = [plan.to_dict() for plan in service.list()]
            payload = {"ok": True, "count": len(plans), "plans": plans}
        else:
            if len(options.args) != 1:
                raise ValueError("plan_id_required")
            plan_id = options.args[0]
            if options.cmd == "agent-plan-show":
                payload = service.load(plan_id).to_dict()
            elif options.cmd == "agent-plan-explain":
                payload = service.explain(plan_id)
            elif options.cmd == "agent-plan-cancel":
                payload = service.cancel(plan_id).to_dict()
            else:
                payload = service.resume(plan_id).to_dict()
        print(json.dumps({"ok": True, **payload}, indent=2, ensure_ascii=False, default=str))
        return 0
    except (KeyError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2
