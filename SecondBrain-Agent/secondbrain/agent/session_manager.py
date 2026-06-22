"""P2 v21.3 - Agent Session Manager."""

from dataclasses import dataclass, field
from time import time


@dataclass
class AgentSession:
    session_id: str
    state: str = "IDLE"
    created_at: float = field(default_factory=time)


class AgentSessionManager:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}

    def create(self, session_id: str) -> AgentSession:
        session = AgentSession(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str):
        return self._sessions.get(session_id)

    def list(self):
        return list(self._sessions.values())
