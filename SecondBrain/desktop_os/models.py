
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any
import time, uuid

@dataclass
class WidgetDefinition:
    widget_id: str
    title: str
    kind: str
    enabled: bool = True
    order: int = 100
    config: dict[str, Any] = field(default_factory=dict)

@dataclass
class Notification:
    notification_id: str
    title: str
    body: str
    level: str = "info"
    read: bool = False
    created_at: float = field(default_factory=time.time)

@dataclass
class CommandDefinition:
    command_id: str
    title: str
    target: str
    description: str = ""
    scopes: list[str] = field(default_factory=list)
    risk_level: int = 1

@dataclass
class DesktopSession:
    session_id: str
    active_view: str = "dashboard"
    selected_project: str | None = None
    last_command: str | None = None
    window_state: dict[str, Any] = field(default_factory=lambda: {"width": 1180, "height": 760, "x": 80, "y": 60})
    updated_at: float = field(default_factory=time.time)

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def to_dict(obj: Any) -> dict[str, Any]:
    return asdict(obj)
