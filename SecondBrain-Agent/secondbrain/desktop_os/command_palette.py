
from __future__ import annotations
from .models import CommandDefinition, to_dict

DEFAULT_COMMANDS = [
    CommandDefinition('open_dashboard', 'Open Dashboard', 'desktop.dashboard', 'Show the desktop dashboard', ['desktop.read'], 1),
    CommandDefinition('quick_capture', 'Quick Capture', 'capture', 'Store a quick note', ['desktop.write'], 1),
    CommandDefinition('ask_jarvis', 'Ask Jarvis', 'ai.ask', 'Ask the AI runtime', ['desktop.write'], 1),
    CommandDefinition('run_swarm', 'Run Swarm Task', 'swarm.run', 'Delegate objective to multi-agent swarm', ['desktop.write','swarm.write'], 2),
    CommandDefinition('search_knowledge', 'Search Knowledge', 'rag.search', 'Search indexed knowledge', ['desktop.read'], 1),
    CommandDefinition('show_status', 'System Status', 'core.status', 'Show OS status', ['desktop.read'], 1),
]

class CommandPalette:
    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry
        self.commands = {c.command_id: c for c in DEFAULT_COMMANDS}

    def list(self, query: str | None = None):
        rows = [to_dict(c) for c in self.commands.values()]
        if query:
            q = query.lower()
            rows = [r for r in rows if q in r['title'].lower() or q in r['command_id'].lower() or q in r.get('description','').lower()]
        return sorted(rows, key=lambda r: r['title'])

    def resolve(self, query: str):
        rows = self.list(query)
        if not rows:
            return None
        exact = [r for r in rows if r['command_id'] == query or r['title'].lower() == query.lower()]
        return exact[0] if exact else rows[0]

    def status(self):
        return {'component': 'command_palette_v125', 'commands': len(self.commands), 'healthy': True}
