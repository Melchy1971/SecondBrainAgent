from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class VoiceEvent:
    type: str
    text: str = ''
    session_id: str = ''
    payload: dict[str, Any] | None = None
    id: str = ''
    ts: str = ''
    def __post_init__(self):
        if not self.id: self.id = 'vevt_' + uuid4().hex[:12]
        if not self.ts: self.ts = now_iso()
        if self.payload is None: self.payload = {}
    def to_dict(self): return asdict(self)

@dataclass
class VoiceSession:
    id: str
    status: str = 'active'
    transcript: list[dict[str, Any]] | None = None
    created_at: str = ''
    updated_at: str = ''
    interrupted: bool = False
    def __post_init__(self):
        if self.transcript is None: self.transcript = []
        if not self.created_at: self.created_at = now_iso()
        if not self.updated_at: self.updated_at = now_iso()
    def to_dict(self): return asdict(self)

@dataclass
class VoiceCommand:
    intent: str
    text: str
    target: str
    payload: dict[str, Any]
    risk: int = 1
    requires_approval: bool = False
    def to_dict(self): return asdict(self)
