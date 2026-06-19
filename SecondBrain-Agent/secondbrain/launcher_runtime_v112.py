from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v111 import SecondBrainLauncherV111, _print_json
from .autonomous_agent_v110 import ToolHost
from .workflow_engine_v112 import WorkflowDefinition, WorkflowEngine, step, workflow_summary
from .specialist_agents_v112 import build_specialist_workflow


class SecondBrainLauncherV112(SecondBrainLauncherV111):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.workflow_host = self._build_workflow_host()
        self.workflow_engine = WorkflowEngine(self.config.runtime_dir, self.workflow_host)

    def _build_workflow_host(self) -> ToolHost:
        host = ToolHost()
        host.register("desktop.quick_capture", lambda payload: {"path": str(self.quick_capture(payload.get("text", ""), payload.get("title", "Workflow Capture")))})
        host.register("desktop.notify", lambda payload: {"path": str(self.notify(payload.get("message", ""), payload.get("severity", "info")))})
        host.register("connectors.sync", lambda payload: {"results": [asdict(r) for r in self.sync_connectors()]})
        host.register("ai.ask", lambda payload: {"answer": self.ask(payload.get("prompt", ""), payload.get("task", "workflow"), payload.get("provider"))})
        host.register("rag.search", lambda payload: {"hits": self.rag_search(payload.get("query", ""), int(payload.get("limit", 8)))})
        host.register("rag.answer", lambda payload: self.rag_answer(payload.get("query", ""), int(payload.get("limit", 5))))
        host.register("workflow.noop", lambda payload: {"ok": True, "payload": payload})
        return host

    def workflow_status(self) -> dict[str, Any]:
        return self.workflow_engine.status()

    def workflow_run(self, name: str, objective: str) -> dict[str, Any]:
        wf = self._named_workflow(name, objective)
        run = self.workflow_engine.run(wf)
        self.emit("workflow.completed", "launcher_v112", workflow_summary(run), risk_level=1)
        return workflow_summary(run)

    def specialist_run(self, agent: str, objective: str) -> dict[str, Any]:
        wf = build_specialist_workflow(agent, objective)
        run = self.workflow_engine.run(wf)
        self.emit("specialist_agent.completed", agent, workflow_summary(run), risk_level=1)
        return workflow_summary(run)

    def _named_workflow(self, name: str, objective: str) -> WorkflowDefinition:
        key = name.strip().lower()
        if key in {"daily", "daily-brief", "brief"}:
            s1 = step("sync_sources", "connectors.sync")
            s2 = step("search_today_context", "rag.search", {"query": f"Tagesbriefing {objective}", "limit": 10}, [s1.step_id])
            s3 = step("write_daily_brief", "rag.answer", {"query": f"Erstelle ein operatives Tagesbriefing: {objective}", "limit": 8}, [s2.step_id])
            s4 = step("save_daily_brief", "desktop.quick_capture", {"title": "Daily Brief", "text": f"Daily Brief Ziel: {objective}"}, [s3.step_id])
            return WorkflowDefinition("workflow.daily.v112", "Daily Brief Workflow", "Sync + RAG + Briefing + Capture", [s1, s2, s3, s4])
        if key in {"project", "project-review", "review"}:
            s1 = step("search_project_context", "rag.search", {"query": f"Projektstatus Risiken nächste Schritte {objective}", "limit": 12})
            s2 = step("project_summary", "rag.answer", {"query": f"Erstelle Projektstatus mit Risiken, Blockern, nächsten Schritten: {objective}", "limit": 8}, [s1.step_id])
            s3 = step("save_project_review", "desktop.quick_capture", {"title": "Project Review", "text": f"Project Review Ziel: {objective}"}, [s2.step_id])
            return WorkflowDefinition("workflow.project_review.v112", "Project Review Workflow", "Projektkontext prüfen und Statusnotiz erzeugen", [s1, s2, s3])
        s1 = step("ask_ai", "ai.ask", {"task": "workflow", "prompt": objective})
        s2 = step("save_result", "desktop.quick_capture", {"title": f"Workflow {name}", "text": objective}, [s1.step_id])
        return WorkflowDefinition(f"workflow.{key}.v112", f"{name} Workflow", "Generic AI + Capture workflow", [s1, s2])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.2 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)

    for cmd in ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status']:
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

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncherV112(args.project_root, args.profile)
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
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
