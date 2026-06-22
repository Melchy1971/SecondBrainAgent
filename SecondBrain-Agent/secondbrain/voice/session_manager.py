"""P6 v24.1 - Voice Session Manager."""

from dataclasses import dataclass, field
from time import time


@dataclass
class VoiceSession:
    session_id: str
    started_at: float = field(default_factory=time)
    active: bool = True


class VoiceSessionManager:
    def __init__(self):
        self._sessions = {}

    def start(self, session_id: str):
        session = VoiceSession(session_id)
        self._sessions[session_id] = session
        return session

    def stop(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].active = False

    def get(self, session_id: str):
        return self._sessions.get(session_id)
