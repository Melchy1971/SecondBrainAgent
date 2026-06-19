from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4
from .json_store import JsonStore
from .models import VoiceEvent, VoiceSession
from .adapters import ManualStreamingSTT, ConsoleStreamingTTS, WakeWordDetector
from .command_router import VoiceCommandRouter
from .memory import VoiceMemory

class RealtimeVoiceRuntime:
    def __init__(self, runtime_dir: str | Path, event_bus: Any = None, tool_registry: Any = None):
        self.root = Path(runtime_dir) / 'voice_v126'
        self.store = JsonStore(self.root)
        self.event_bus = event_bus
        self.tool_registry = tool_registry
        self.stt = ManualStreamingSTT()
        self.tts = ConsoleStreamingTTS()
        self.wake = WakeWordDetector()
        self.router = VoiceCommandRouter()
        self.memory = VoiceMemory(self.store)

    def status(self) -> dict[str, Any]:
        sessions = self.store.read('sessions', {})
        return {'component': 'voice_realtime_v126', 'healthy': True, 'root': str(self.root), 'sessions': len(sessions), 'memory': self.memory.status(), 'stt': self.stt.name, 'tts': self.tts.name, 'wake_words': self.wake.wake_words}

    def publish_event(self, event: VoiceEvent):
        self.store.append('events', event.to_dict(), limit=2000)
        if self.event_bus is not None and hasattr(self.event_bus, 'publish'):
            try: self.event_bus.publish('voice.event', event.to_dict())
            except TypeError: pass
        return event.to_dict()

    def start_session(self) -> dict[str, Any]:
        sid = 'vs_' + uuid4().hex[:12]
        session = VoiceSession(id=sid)
        sessions = self.store.read('sessions', {})
        sessions[sid] = session.to_dict(); self.store.write('sessions', sessions)
        self.publish_event(VoiceEvent('session.started', session_id=sid))
        return sessions[sid]

    def sessions(self) -> list[dict[str, Any]]:
        return list(self.store.read('sessions', {}).values())

    def get_session(self, session_id: str | None = None) -> dict[str, Any]:
        sessions = self.store.read('sessions', {})
        if session_id and session_id in sessions: return sessions[session_id]
        active = [s for s in sessions.values() if s.get('status') == 'active']
        if active: return active[-1]
        return self.start_session()

    def interrupt(self, session_id: str | None = None, reason: str = 'manual_interrupt') -> dict[str, Any]:
        session = self.get_session(session_id)
        sessions = self.store.read('sessions', {})
        session['interrupted'] = True; session['status'] = 'interrupted'; session['interrupt_reason'] = reason
        sessions[session['id']] = session; self.store.write('sessions', sessions)
        self.publish_event(VoiceEvent('session.interrupted', session_id=session['id'], payload={'reason': reason}))
        return session

    def detect_wake(self, text: str) -> dict[str, Any]:
        result = self.wake.detect(text)
        self.publish_event(VoiceEvent('wake.detected' if result['detected'] else 'wake.missed', text=text, payload=result))
        return result

    def transcribe(self, chunks: Iterable[str], session_id: str | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        text = self.stt.transcribe_chunks(chunks)
        event = VoiceEvent('speech.transcribed', text=text, session_id=session['id'])
        self.publish_event(event)
        self._append_transcript(session['id'], {'role': 'user', 'text': text, 'event_id': event.id})
        self.memory.remember({'type': 'transcript', 'session_id': session['id'], 'text': text})
        return {'session_id': session['id'], 'text': text, 'event': event.to_dict()}

    def parse(self, text: str) -> dict[str, Any]:
        command = self.router.parse(text)
        self.publish_event(VoiceEvent('command.parsed', text=text, payload=command.to_dict()))
        return command.to_dict()

    def speak(self, text: str, session_id: str | None = None) -> dict[str, Any]:
        session = self.get_session(session_id)
        spoken = self.tts.speak(text)
        event = VoiceEvent('speech.spoken', text=text, session_id=session['id'], payload=spoken)
        self.publish_event(event)
        self._append_transcript(session['id'], {'role': 'assistant', 'text': text, 'event_id': event.id})
        return {'session_id': session['id'], 'speech': spoken, 'event': event.to_dict()}

    def handle(self, text: str, approved: bool = False, session_id: str | None = None) -> dict[str, Any]:
        wake = self.detect_wake(text)
        session = self.get_session(session_id)
        transcription = self.transcribe([text], session['id'])
        command = self.router.parse(transcription['text'])
        if command.requires_approval and not approved:
            response = {'status': 'approval_required', 'command': command.to_dict()}
            self.publish_event(VoiceEvent('command.blocked.approval_required', text=text, session_id=session['id'], payload=response))
            return response
        result = {'status': 'accepted', 'command': command.to_dict()}
        if self.tool_registry is not None and '.' in command.target:
            try:
                result['tool_result'] = self.tool_registry.execute(command.target, command.payload, scopes=['voice.execute'], approved=approved)
            except Exception as exc:
                result['tool_error'] = str(exc)
        self.publish_event(VoiceEvent('command.accepted', text=text, session_id=session['id'], payload=result))
        return {'wake': wake, **result}

    def events(self, limit: int = 50): return self.store.read('events', [])[-limit:]
    def recent_memory(self, limit: int = 20): return self.memory.recent(limit)

    def _append_transcript(self, session_id: str, item: dict[str, Any]):
        sessions = self.store.read('sessions', {})
        session = sessions.get(session_id) or VoiceSession(id=session_id).to_dict()
        session.setdefault('transcript', []).append(item)
        sessions[session_id] = session
        self.store.write('sessions', sessions)
