from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse, json
from .launcher_runtime_v125 import SecondBrainLauncherV125
from .launcher_runtime_v113 import _print_json
from .tool_registry_v121 import ToolDefinition
from .voice_realtime import RealtimeVoiceRuntime

class SecondBrainLauncherV126(SecondBrainLauncherV125):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.voice_v126 = RealtimeVoiceRuntime(self.config.runtime_dir, event_bus=getattr(self, 'event_bus_v121', None), tool_registry=self.tool_registry_v121)
        self._register_voice_tools()

    def _register_voice_tools(self):
        defs = [
            ToolDefinition('voice.status.v126','Read realtime voice status',{'type':'object','properties':{}},{'type':'object'},['voice.read'],1,False),
            ToolDefinition('voice.handle.v126','Handle spoken text',{'type':'object','required':['text'],'properties':{'text':{'type':'string'},'approved':{'type':'boolean'}}},{'type':'object'},['voice.execute'],2,False),
            ToolDefinition('voice.speak.v126','Speak text through configured TTS',{'type':'object','required':['text'],'properties':{'text':{'type':'string'}}},{'type':'object'},['voice.write'],1,False),
        ]
        handlers = {
            'voice.status.v126': lambda p: self.voice_status_v126(),
            'voice.handle.v126': lambda p: self.voice_handle_v126(p.get('text',''), p.get('approved', False)),
            'voice.speak.v126': lambda p: self.voice_speak_v126(p.get('text','')),
        }
        for d in defs: self.tool_registry_v121.register(d, handlers[d.name])

    def voice_status_v126(self): return self.voice_v126.status()
    def voice_session_v126(self): return self.voice_v126.start_session()
    def voice_sessions_v126(self): return self.voice_v126.sessions()
    def voice_wake_v126(self, text: str): return self.voice_v126.detect_wake(text)
    def voice_transcribe_v126(self, chunks: list[str]): return self.voice_v126.transcribe(chunks)
    def voice_parse_v126(self, text: str): return self.voice_v126.parse(text)
    def voice_handle_v126(self, text: str, approved: bool = False): return self.voice_v126.handle(text, approved=approved)
    def voice_speak_v126(self, text: str): return self.voice_v126.speak(text)
    def voice_interrupt_v126(self, session_id: str | None = None, reason: str = 'manual_interrupt'): return self.voice_v126.interrupt(session_id, reason)
    def voice_events_v126(self, limit: int = 50): return self.voice_v126.events(limit)
    def voice_memory_v126(self, limit: int = 20): return self.voice_v126.recent_memory(limit)
    def core126_status(self):
        base = self.core125_status(); base.update({'version':'12.6','voice_realtime': self.voice_status_v126()}); return base

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.6 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()))
    parser.add_argument('--profile', default=None)
    sub = parser.add_subparsers(dest='cmd', required=False)
    for cmd in ['core-status','voice-status2','voice-session2','voice-sessions2','voice-events','voice-memory']:
        sub.add_parser(cmd)
    p=sub.add_parser('voice-wake'); p.add_argument('text')
    p=sub.add_parser('voice-transcribe'); p.add_argument('chunks', nargs='+')
    p=sub.add_parser('voice-parse2'); p.add_argument('text')
    p=sub.add_parser('voice-handle2'); p.add_argument('text'); p.add_argument('--approved', action='store_true')
    p=sub.add_parser('voice-speak2'); p.add_argument('text')
    p=sub.add_parser('voice-interrupt'); p.add_argument('--session-id', default=None); p.add_argument('--reason', default='manual_interrupt')
    return parser

def main(argv: list[str] | None = None) -> int:
    import sys
    raw=list(sys.argv[1:] if argv is None else argv)
    v126_cmds={'core-status','voice-status2','voice-session2','voice-sessions2','voice-wake','voice-transcribe','voice-parse2','voice-handle2','voice-speak2','voice-interrupt','voice-events','voice-memory'}
    first_cmd=next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in v126_cmds:
        from .launcher_runtime_v125 import main as legacy_main
        return legacy_main(argv)
    parser=build_parser(); args=parser.parse_args(argv); cmd=args.cmd or 'core-status'
    launcher=SecondBrainLauncherV126(args.project_root, args.profile)
    try:
        if cmd=='core-status': _print_json(launcher.core126_status())
        elif cmd=='voice-status2': _print_json(launcher.voice_status_v126())
        elif cmd=='voice-session2': _print_json(launcher.voice_session_v126())
        elif cmd=='voice-sessions2': _print_json(launcher.voice_sessions_v126())
        elif cmd=='voice-wake': _print_json(launcher.voice_wake_v126(args.text))
        elif cmd=='voice-transcribe': _print_json(launcher.voice_transcribe_v126(args.chunks))
        elif cmd=='voice-parse2': _print_json(launcher.voice_parse_v126(args.text))
        elif cmd=='voice-handle2': _print_json(launcher.voice_handle_v126(args.text, args.approved))
        elif cmd=='voice-speak2': _print_json(launcher.voice_speak_v126(args.text))
        elif cmd=='voice-interrupt': _print_json(launcher.voice_interrupt_v126(args.session_id, args.reason))
        elif cmd=='voice-events': _print_json(launcher.voice_events_v126())
        elif cmd=='voice-memory': _print_json(launcher.voice_memory_v126())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1

if __name__ == '__main__': raise SystemExit(main())
