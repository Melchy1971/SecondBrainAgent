from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v113 import SecondBrainLauncherV113, _print_json
from .voice_runtime_v114 import VoiceRuntime, VoiceCommand


class SecondBrainLauncherV114(SecondBrainLauncherV113):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.voice_runtime = VoiceRuntime(self.config.runtime_dir, self.execute_voice_command)
        self.workflow_host.register("voice.status", lambda payload: self.voice_status())
        self.workflow_host.register("voice.handle", lambda payload: self.voice_handle(payload.get("text", ""), payload.get("session_id")))

    def execute_voice_command(self, command: VoiceCommand) -> Any:
        intent = command.intent
        args = command.args
        if intent == "runtime.status":
            return self.runtime_status()
        if intent == "runtime.health":
            return self.health()
        if intent == "runtime.diagnose":
            return self.diagnose()
        if intent == "runtime.metrics":
            return self.metrics()
        if intent == "runtime.down":
            return self.down()
        if intent == "capture.note":
            return {"path": self.quick_capture(args.get("text", ""), args.get("title", "Voice Capture")), "status": "captured"}
        if intent == "rag.search":
            return {"results": self.rag_search(args.get("query", ""), int(args.get("limit", 5))), "status": "searched"}
        if intent == "ai.ask":
            return {"answer": self.ask(args.get("prompt", ""), args.get("task", "voice")), "status": "answered"}
        if intent == "agent.run":
            return self.autonomous_run(args.get("objective", ""), int(args.get("max_steps", 5)))
        if intent == "workflow.run":
            return self.workflow_run(args.get("name", "voice_workflow"), args.get("objective", ""))
        return {"status": "unknown_intent", "intent": intent}

    def voice_status(self) -> dict[str, Any]:
        return self.voice_runtime.status()

    def voice_configure(self, wake_word: str | None = None, mode: str | None = None, allow_system_actions: bool | None = None) -> dict[str, Any]:
        return self.voice_runtime.configure(wake_word=wake_word, mode=mode, allow_system_actions=allow_system_actions)

    def voice_parse(self, text: str) -> dict[str, Any]:
        return self.voice_runtime.parse(text)

    def voice_say(self, text: str) -> dict[str, Any]:
        return self.voice_runtime.say(text)

    def voice_session(self) -> dict[str, Any]:
        return self.voice_runtime.open_session()

    def voice_sessions(self) -> list[dict[str, Any]]:
        return self.voice_runtime.list_sessions()

    def voice_handle(self, text: str, session_id: str | None = None, no_execute: bool = False) -> dict[str, Any]:
        result = self.voice_runtime.handle_text(text, session_id=session_id, auto_execute=not no_execute)
        self.emit("voice.command_handled", "launcher_v114", {
            "intent": result["command"]["intent"],
            "executed": result["executed"],
            "blocked": result["blocked"],
        }, risk_level=2 if result["blocked"] else 1)
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.4 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)

    for cmd in ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions']:
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
    p_vparse = sub.add_parser('voice-parse'); p_vparse.add_argument('text')
    p_vsay = sub.add_parser('voice-say'); p_vsay.add_argument('text')
    p_vhandle = sub.add_parser('voice-handle'); p_vhandle.add_argument('text'); p_vhandle.add_argument('--session-id', default=None); p_vhandle.add_argument('--no-execute', action='store_true')
    p_vcfg = sub.add_parser('voice-config'); p_vcfg.add_argument('--wake-word', default=None); p_vcfg.add_argument('--mode', default=None); p_vcfg.add_argument('--allow-system-actions', action='store_true')

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncherV114(args.project_root, args.profile)
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
        elif cmd == 'voice-status': _print_json(launcher.voice_status())
        elif cmd == 'voice-session': _print_json(launcher.voice_session())
        elif cmd == 'voice-sessions': _print_json(launcher.voice_sessions())
        elif cmd == 'voice-parse': _print_json(launcher.voice_parse(args.text))
        elif cmd == 'voice-say': _print_json(launcher.voice_say(args.text))
        elif cmd == 'voice-handle': _print_json(launcher.voice_handle(args.text, args.session_id, args.no_execute))
        elif cmd == 'voice-config': _print_json(launcher.voice_configure(args.wake_word, args.mode, True if args.allow_system_actions else None))
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
