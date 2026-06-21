DEFAULT_COMMANDS = [
    {"id": "open_dashboard", "title": "Open Dashboard", "target": "desktop.dashboard"},
    {"id": "open_knowledge", "title": "Open Knowledge Explorer", "target": "desktop.knowledge"},
    {"id": "open_memory", "title": "Open Memory Explorer", "target": "desktop.memory"},
    {"id": "open_kanban", "title": "Open Kanban", "target": "desktop.kanban"},
    {"id": "quick_capture", "title": "Quick Capture", "target": "capture.quick"},
    {"id": "run_agent", "title": "Run Agent", "target": "agent.run"},
]


class CommandPalette:
    def __init__(self, store):
        self.store = store

    def commands(self) -> list[dict]:
        cmds = self.store.load("commands", None)
        if cmds is None:
            self.store.save("commands", DEFAULT_COMMANDS)
            return DEFAULT_COMMANDS
        return cmds

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [c for c in self.commands() if q in c["title"].lower() or q in c["id"].lower() or q in c["target"].lower()]

    def execute(self, command_id: str) -> dict:
        command = next((c for c in self.commands() if c["id"] == command_id), None)
        if not command:
            return {"ok": False, "error": "command_not_found", "command_id": command_id}
        return self.store.append("command_history", {"ok": True, "command": command})
