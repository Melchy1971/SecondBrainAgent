
from __future__ import annotations
from pathlib import Path
from typing import Any, Callable
from .json_store import JsonStore
from .widget_registry import WidgetRegistry
from .notification_center import NotificationCenter
from .command_palette import CommandPalette
from .session_manager import DesktopSessionManager
from .dashboard import DashboardBackend

class DesktopOSKernel:
    def __init__(self, runtime_dir: str | Path, tool_registry: Any = None, service_status_provider: Callable[[], dict[str, Any]] | None = None):
        self.root = Path(runtime_dir) / 'desktop_v125'
        self.store = JsonStore(self.root)
        self.tool_registry = tool_registry
        self.service_status_provider = service_status_provider
        self.widgets = WidgetRegistry(self.store)
        self.notifications = NotificationCenter(self.store)
        self.commands = CommandPalette(tool_registry)
        self.sessions = DesktopSessionManager(self.store)
        self.dashboard = DashboardBackend(self)

    def status(self):
        return {
            'component': 'desktop_os_v125',
            'healthy': True,
            'root': str(self.root),
            'widgets': self.widgets.status(),
            'notifications': self.notifications.status(),
            'commands': self.commands.status(),
            'session': self.sessions.status(),
        }

    def open(self, view: str = 'dashboard'):
        session = self.sessions.update(active_view=view)
        self.notifications.notify('Desktop opened', f'Active view: {view}', 'success')
        return {'status': 'opened', 'view': view, 'session': session}

    def quick_capture(self, text: str, title: str = 'Quick Capture'):
        note = {'title': title, 'text': text.strip(), 'source': 'desktop_v125'}
        self.notifications.notify('Quick capture stored', title, 'success')
        return {'status': 'captured', 'note': note}

    def execute_command(self, command_id: str, payload: dict[str, Any] | None = None):
        payload = payload or {}
        command = self.commands.resolve(command_id)
        if command is None:
            raise KeyError(f'Unknown desktop command: {command_id}')
        self.sessions.update(last_command=command['command_id'])
        if command['target'] == 'desktop.dashboard':
            result = self.dashboard.snapshot()
        elif command['target'] == 'capture':
            result = self.quick_capture(payload.get('text', ''), payload.get('title', 'Quick Capture'))
        elif self.tool_registry is not None:
            result = self.tool_registry.execute(command['target'], payload, scopes=command.get('scopes', []), approved=payload.get('approved', False))
        else:
            result = {'status': 'accepted', 'target': command['target'], 'payload': payload}
        return {'command': command, 'result': result}
