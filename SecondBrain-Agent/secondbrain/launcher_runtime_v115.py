
from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .launcher_runtime_v114 import SecondBrainLauncherV114
from .launcher_runtime_v113 import _print_json
from .mobile_bridge_v115 import MobileBridge


class SecondBrainLauncherV115(SecondBrainLauncherV114):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.mobile_bridge = MobileBridge(self.config.runtime_dir)
        self.workflow_host.register("mobile.status", lambda payload: self.mobile_status())
        self.workflow_host.register("mobile.push", lambda payload: self.mobile_push(payload.get("device_id", ""), payload.get("title", "Jarvis"), payload.get("body", ""), payload.get("kind", "notification"), payload.get("payload", {})))
        self.workflow_host.register("mobile.capture", lambda payload: self.mobile_capture(payload.get("device_id", ""), payload.get("type", "note"), payload.get("title", "Mobile Capture"), payload.get("content", ""), payload.get("metadata", {})))

    def mobile_status(self) -> dict[str, Any]:
        return self.mobile_bridge.status()

    def mobile_register(self, name: str, platform: str, capabilities: str = "capture,push,approval", trusted: bool = False) -> dict[str, Any]:
        caps = [c.strip() for c in capabilities.split(",") if c.strip()]
        device = self.mobile_bridge.register_device(name, platform, caps, trusted)
        self.emit("mobile.device_registered", "launcher_v115", {"device_id": device["device_id"], "platform": platform}, risk_level=1)
        return device

    def mobile_devices(self) -> list[dict[str, Any]]:
        return self.mobile_bridge.list_devices()

    def mobile_trust(self, device_id: str, trusted: bool = True) -> dict[str, Any]:
        device = self.mobile_bridge.trust_device(device_id, trusted)
        self.emit("mobile.device_trust_changed", "launcher_v115", {"device_id": device_id, "trusted": trusted}, risk_level=2)
        return device

    def mobile_push(self, device_id: str, title: str, body: str, kind: str = "notification", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        msg = self.mobile_bridge.enqueue_push(device_id, title, body, kind, payload)
        self.emit("mobile.push_queued", "launcher_v115", {"message_id": msg["message_id"], "device_id": device_id, "kind": kind}, risk_level=1)
        return msg

    def mobile_push_list(self, device_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        return self.mobile_bridge.list_push(device_id, status)

    def mobile_push_delivered(self, message_id: str) -> dict[str, Any]:
        return self.mobile_bridge.mark_push_delivered(message_id)

    def mobile_capture(self, device_id: str, capture_type: str, title: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        capture = self.mobile_bridge.submit_capture(device_id, capture_type, title, content, metadata)
        self.emit("mobile.capture_received", "launcher_v115", {"capture_id": capture["capture_id"], "type": capture_type}, risk_level=1)
        return capture

    def mobile_captures(self, unprocessed_only: bool = False) -> list[dict[str, Any]]:
        return self.mobile_bridge.list_captures(unprocessed_only)

    def mobile_approval_request(self, device_id: str, action: str, reason: str, payload: str = "{}", risk: int = 3) -> dict[str, Any]:
        approval = self.mobile_bridge.request_approval(device_id, action, json.loads(payload), reason, risk)
        self.emit("mobile.approval_requested", "launcher_v115", {"approval_id": approval["approval_id"], "action": action, "risk": risk}, risk_level=risk)
        return approval

    def mobile_approvals(self, status: str | None = "pending") -> list[dict[str, Any]]:
        return self.mobile_bridge.list_approvals(status)

    def mobile_approval_decide(self, approval_id: str, decision: str, note: str = "") -> dict[str, Any]:
        approval = self.mobile_bridge.decide_approval(approval_id, decision, note)
        self.emit("mobile.approval_decided", "launcher_v115", {"approval_id": approval_id, "decision": decision}, risk_level=2)
        return approval


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v11.5 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()), help='SecondBrain-Agent Projektordner')
    parser.add_argument('--profile', default=None, help='Startprofil, z. B. safe/dev/local-ai')
    sub = parser.add_subparsers(dest='cmd', required=False)

    base_cmds = ['init','health','sync','tick','start','rag-index','agent-status','up','down','status','restart','diagnose','metrics','recover','workflow-status','twin-status','decision-history','voice-status','voice-session','voice-sessions','mobile-status','mobile-devices','mobile-push-list','mobile-captures','mobile-approvals']
    for cmd in base_cmds:
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
    p_mreg = sub.add_parser('mobile-register'); p_mreg.add_argument('name'); p_mreg.add_argument('platform'); p_mreg.add_argument('--capabilities', default='capture,push,approval'); p_mreg.add_argument('--trusted', action='store_true')
    p_mtrust = sub.add_parser('mobile-trust'); p_mtrust.add_argument('device_id'); p_mtrust.add_argument('--untrust', action='store_true')
    p_mpush = sub.add_parser('mobile-push'); p_mpush.add_argument('device_id'); p_mpush.add_argument('title'); p_mpush.add_argument('body'); p_mpush.add_argument('--kind', default='notification'); p_mpush.add_argument('--payload', default='{}')
    p_mdel = sub.add_parser('mobile-push-delivered'); p_mdel.add_argument('message_id')
    p_mcap = sub.add_parser('mobile-capture'); p_mcap.add_argument('device_id'); p_mcap.add_argument('capture_type'); p_mcap.add_argument('title'); p_mcap.add_argument('content'); p_mcap.add_argument('--metadata', default='{}')
    p_mreq = sub.add_parser('mobile-approval-request'); p_mreq.add_argument('device_id'); p_mreq.add_argument('action'); p_mreq.add_argument('reason'); p_mreq.add_argument('--payload', default='{}'); p_mreq.add_argument('--risk', type=int, default=3)
    p_mdec = sub.add_parser('mobile-approval-decide'); p_mdec.add_argument('approval_id'); p_mdec.add_argument('decision', choices=['approved','rejected']); p_mdec.add_argument('--note', default='')

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncherV115(args.project_root, args.profile)
    cmd = args.cmd or 'status'
    try:
        if cmd == 'mobile-status': _print_json(launcher.mobile_status())
        elif cmd == 'mobile-register': _print_json(launcher.mobile_register(args.name, args.platform, args.capabilities, args.trusted))
        elif cmd == 'mobile-devices': _print_json(launcher.mobile_devices())
        elif cmd == 'mobile-trust': _print_json(launcher.mobile_trust(args.device_id, not args.untrust))
        elif cmd == 'mobile-push': _print_json(launcher.mobile_push(args.device_id, args.title, args.body, args.kind, json.loads(args.payload)))
        elif cmd == 'mobile-push-list': _print_json(launcher.mobile_push_list())
        elif cmd == 'mobile-push-delivered': _print_json(launcher.mobile_push_delivered(args.message_id))
        elif cmd == 'mobile-capture': _print_json(launcher.mobile_capture(args.device_id, args.capture_type, args.title, args.content, json.loads(args.metadata)))
        elif cmd == 'mobile-captures': _print_json(launcher.mobile_captures())
        elif cmd == 'mobile-approval-request': _print_json(launcher.mobile_approval_request(args.device_id, args.action, args.reason, args.payload, args.risk))
        elif cmd == 'mobile-approvals': _print_json(launcher.mobile_approvals())
        elif cmd == 'mobile-approval-decide': _print_json(launcher.mobile_approval_decide(args.approval_id, args.decision, args.note))
        else:
            # Delegate legacy commands to the v11.4 CLI implementation to avoid behavior drift.
            from .launcher_runtime_v114 import main as legacy_main
            return legacy_main(argv)
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
