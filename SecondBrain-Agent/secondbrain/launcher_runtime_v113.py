from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v112 import SecondBrainLauncherV112, _print_json
from .digital_twin_v113 import DigitalTwin, parse_scenario_change
from .decision_engine_v113 import DecisionEngine, parse_option


class SecondBrainLauncherV113(SecondBrainLauncherV112):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.digital_twin = DigitalTwin(self.config.runtime_dir)
        self.decision_engine = DecisionEngine(self.config.runtime_dir, self.digital_twin)
        self.workflow_host.register("twin.snapshot", lambda payload: self.twin_snapshot())
        self.workflow_host.register("twin.simulate", lambda payload: self.twin_simulate(payload.get("name", "Workflow Scenario"), payload.get("changes", [])))
        self.workflow_host.register("decision.evaluate", lambda payload: self.decision_evaluate(payload.get("question", "Decision"), payload.get("options", [])))

    def twin_snapshot(self) -> dict[str, Any]:
        return self.digital_twin.snapshot()

    def twin_capacity(self, weekly: float, fixed: float = 0.0, buffer: float = 5.0) -> dict[str, Any]:
        budget = self.digital_twin.set_capacity(weekly, fixed, buffer)
        self.emit("digital_twin.capacity_updated", "launcher_v113", asdict(budget), risk_level=1)
        return asdict(budget) | {"usable_hours": budget.usable_hours}

    def twin_add_project(self, name: str, hours: float, priority: int = 3, risk: int = 1) -> dict[str, Any]:
        project = self.digital_twin.add_project(name, hours, priority, risk)
        self.emit("digital_twin.project_added", "launcher_v113", asdict(project), risk_level=1)
        return asdict(project)

    def twin_add_goal(self, name: str, target: float | None = None, current: float | None = None, unit: str = "", priority: int = 3, deadline: str = "") -> dict[str, Any]:
        goal = self.digital_twin.add_goal(name, target, current, unit, priority, deadline)
        self.emit("digital_twin.goal_added", "launcher_v113", asdict(goal), risk_level=1)
        return asdict(goal)

    def twin_simulate(self, name: str, changes: list[Any]) -> dict[str, Any]:
        parsed = []
        for c in changes:
            if isinstance(c, str):
                parsed.append(parse_scenario_change(c))
            elif isinstance(c, dict):
                parsed.append(parse_scenario_change(f"{c.get('name','Change')}:{c.get('weekly_hours',1)}:{c.get('risk_level',2)}"))
        result = self.digital_twin.simulate(name, parsed)
        self.emit("digital_twin.scenario_simulated", "launcher_v113", asdict(result), risk_level=min(4, max(1, result.risk_score // 2)))
        return asdict(result)

    def decision_evaluate(self, question: str, options: list[Any]) -> dict[str, Any]:
        parsed = []
        for option in options:
            if isinstance(option, str):
                parsed.append(parse_option(option))
            elif isinstance(option, dict):
                parsed.append(parse_option(
                    f"{option.get('name','Option')}:{option.get('weekly_hours',0)}:{option.get('expected_value',3)}:{option.get('risk_level',2)}:{option.get('strategic_fit',3)}:{option.get('reversibility',3)}"
                ))
        result = self.decision_engine.evaluate(question, parsed)
        self.emit("decision.evaluated", "launcher_v113", asdict(result), risk_level=2)
        return asdict(result)

    def decision_history(self) -> list[dict[str, Any]]:
        return self.decision_engine.history()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.3 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)

    for cmd in ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history']:
        sub.add_parser(cmd)

    p_gui = sub.add_parser('gui'); p_gui.add_argument('--snapshot', action='store_true')
    p_rag_search = sub.add_parser('rag-search'); p_rag_search.add_argument('query'); p_rag_search.add_argument('--limit', type=int, default=8)
    p_rag_answer = sub.add_parser('rag-answer'); p_rag_answer.add_argument('query'); p_rag_answer.add_argument('--limit', type=int, default=5); p_rag_answer.add_argument('--write', action='store_true')
    p_agent_run = sub.add_parser('agent-run'); p_agent_run.add_argument('objective'); p_agent_run.add_argument('--max-steps', type=int, default=5)
    p_loop = sub.add_parser('loop'); p_loop.add_argument('--interval', type=int, default=30); p_loop.add_argument('--max-cycles', type=int, default=None)
    p_ask = sub.add_parser('ask'); p_ask.add_argument('prompt'); p_ask.add_argument('--task', default='default'); p_ask.add_argument('--provider', default=None)
    p_capture = sub.add_parser('capture'); p_capture.add_argument('text'); p_capture.add_argument('--title', default='Quick Capture')
    p_notify = sub.add_parser('notify'); p_notify.add_argument('message'); p_notify.add_argument('--severity', default='info')
    p_submit = sub.add_parser('submit'); p_submit.add_argument('action'); p_submit.add_argument('payload', nargs='?', default='{}')
    p_workflow = sub.add_parser('workflow-run'); p_workflow.add_argument('name'); p_workflow.add_argument('objective')
    p_spec = sub.add_parser('specialist-run'); p_spec.add_argument('agent', choices=['email','calendar','research','docs','documentation']); p_spec.add_argument('objective')
    p_email = sub.add_parser('email-agent'); p_email.add_argument('objective')
    p_cal = sub.add_parser('calendar-agent'); p_cal.add_argument('objective')
    p_res = sub.add_parser('research-agent'); p_res.add_argument('objective')
    p_doc = sub.add_parser('docs-agent'); p_doc.add_argument('objective')
    p_cap = sub.add_parser('twin-capacity'); p_cap.add_argument('weekly', type=float); p_cap.add_argument('--fixed', type=float, default=0.0); p_cap.add_argument('--buffer', type=float, default=5.0)
    p_proj = sub.add_parser('twin-add-project'); p_proj.add_argument('name'); p_proj.add_argument('hours', type=float); p_proj.add_argument('--priority', type=int, default=3); p_proj.add_argument('--risk', type=int, default=1)
    p_goal = sub.add_parser('twin-add-goal'); p_goal.add_argument('name'); p_goal.add_argument('--target', type=float, default=None); p_goal.add_argument('--current', type=float, default=None); p_goal.add_argument('--unit', default=''); p_goal.add_argument('--priority', type=int, default=3); p_goal.add_argument('--deadline', default='')
    p_sim = sub.add_parser('twin-simulate'); p_sim.add_argument('name'); p_sim.add_argument('changes', nargs='*', help='Format: Name:hours:risk')
    p_dec = sub.add_parser('decision-evaluate'); p_dec.add_argument('question'); p_dec.add_argument('options', nargs='+', help='Format: Name:hours:value:risk:fit:reversible')

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncherV113(args.project_root, args.profile)
    cmd = args.cmd or 'status'
    try:
        if cmd == 'init': _print_json(launcher.init_runtime())
        elif cmd == 'health': _print_json(launcher.health())
        elif cmd == 'sync': _print_json([asdict(r) for r in launcher.sync_connectors()])
        elif cmd == 'tick': _print_json(launcher.tick())
        elif cmd == 'start': _print_json(launcher.start_once())
        elif cmd == 'up': _print_json(launcher.up())
        elif cmd == 'down': _print_json(launcher.down())
        elif cmd == 'status': _print_json(launcher.runtime_status())
        elif cmd == 'restart': _print_json(launcher.restart_runtime())
        elif cmd == 'diagnose': _print_json(launcher.diagnose())
        elif cmd == 'metrics': _print_json(launcher.metrics())
        elif cmd == 'recover': _print_json(launcher.recover())
        elif cmd == 'gui':
            result = launcher.gui(snapshot=args.snapshot)
            if result not in (None, 0): print(result)
        elif cmd == 'rag-index': _print_json(launcher.rag_index())
        elif cmd == 'agent-status': _print_json(launcher.autonomous_status())
        elif cmd == 'rag-search': _print_json(launcher.rag_search(args.query, args.limit))
        elif cmd == 'rag-answer':
            if args.write: print(launcher.rag_write_answer(args.query, args.limit))
            else: _print_json(launcher.rag_answer(args.query, args.limit))
        elif cmd == 'agent-run': _print_json(launcher.autonomous_run(args.objective, args.max_steps))
        elif cmd == 'loop': launcher.start_loop(args.interval, args.max_cycles)
        elif cmd == 'ask': print(launcher.ask(args.prompt, args.task, args.provider))
        elif cmd == 'capture': print(launcher.quick_capture(args.text, args.title))
        elif cmd == 'notify': print(launcher.notify(args.message, args.severity))
        elif cmd == 'submit': _print_json(asdict(launcher.submit(args.action, json.loads(args.payload))))
        elif cmd == 'workflow-status': _print_json(launcher.workflow_status())
        elif cmd == 'workflow-run': _print_json(launcher.workflow_run(args.name, args.objective))
        elif cmd == 'specialist-run': _print_json(launcher.specialist_run(args.agent, args.objective))
        elif cmd == 'email-agent': _print_json(launcher.specialist_run('email', args.objective))
        elif cmd == 'calendar-agent': _print_json(launcher.specialist_run('calendar', args.objective))
        elif cmd == 'research-agent': _print_json(launcher.specialist_run('research', args.objective))
        elif cmd == 'docs-agent': _print_json(launcher.specialist_run('docs', args.objective))
        elif cmd == 'twin-status': _print_json(launcher.twin_snapshot())
        elif cmd == 'twin-capacity': _print_json(launcher.twin_capacity(args.weekly, args.fixed, args.buffer))
        elif cmd == 'twin-add-project': _print_json(launcher.twin_add_project(args.name, args.hours, args.priority, args.risk))
        elif cmd == 'twin-add-goal': _print_json(launcher.twin_add_goal(args.name, args.target, args.current, args.unit, args.priority, args.deadline))
        elif cmd == 'twin-simulate': _print_json(launcher.twin_simulate(args.name, args.changes))
        elif cmd == 'decision-evaluate': _print_json(launcher.decision_evaluate(args.question, args.options))
        elif cmd == 'decision-history': _print_json(launcher.decision_history())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
